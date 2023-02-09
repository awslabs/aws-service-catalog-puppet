import multiprocessing
import os
import queue
import time
import traceback

import networkx as nx

from servicecatalog_puppet import serialisation_utils
from servicecatalog_puppet.waluigi.constants import (
    COMPLETED,
    ERRORED,
    QUEUE_STATUS,
    CONTROL_EVENT__COMPLETE,
)
from servicecatalog_puppet.waluigi.dag_utils import build_the_dag, logger
from servicecatalog_puppet.waluigi.locks.external import (
    are_resources_are_free_for_task,
    lock_resources_for_task,
    unlock_resources_for_task,
)
from servicecatalog_puppet.waluigi.shared_tasks import task_processing_time
from servicecatalog_puppet.waluigi.shared_tasks import task_trace
from servicecatalog_puppet.workflow.dependencies import task_factory
from servicecatalog_puppet.workflow.tasks import unwrap


def worker_task(
    thread_name,
    lock,
    task_queue,
    results_queue,
    task_processing_time_queue,
    task_trace_queue,
    tasks_to_run,
    manifest_files_path,
    manifest_task_reference_file_path,
    puppet_account_id,
    resources_file_path,
):
    logger.info(f"starting up")
    should_be_running = True
    while should_be_running:
        try:
            task_reference = task_queue.get(timeout=5)
        except queue.Empty:
            continue

        else:
            result = False
            while not result:
                # print(
                #     f"{thread_name} Worker received {task_reference} waiting for lock",
                #     flush=True,
                # )
                task_parameters = tasks_to_run.get(task_reference)
                # print(
                #     f"{pid} Worker received {task_reference} waiting for lock and the task is {task_parameters}",
                #     flush=True,
                # )

                with lock:
                    # print(f"{pid} Worker {task_reference} got the lock", flush=True)
                    (
                        resources_are_free,
                        resources_in_use,
                    ) = are_resources_are_free_for_task(
                        task_parameters, resources_file_path
                    )
                    # print(
                    #     f"{pid} Worker {task_reference} resources_are_free: {resources_are_free}",
                    #     flush=True,
                    # )
                    if resources_are_free:
                        lock_resources_for_task(
                            task_reference,
                            task_parameters,
                            resources_in_use,
                            resources_file_path,
                        )
                        # print(f"{pid} Worker {task_reference} locked", flush=True)

                if resources_are_free:
                    # print(f"{pid} Worker about to run {task_reference}", flush=True)
                    task = task_factory.create(
                        manifest_files_path=manifest_files_path,
                        manifest_task_reference_file_path=manifest_task_reference_file_path,
                        puppet_account_id=puppet_account_id,
                        parameters_to_use=task_parameters,
                    )
                    logger.info(f"executing task: {task_reference}")
                    task.on_task_start()
                    start = time.time()
                    task_type, task_details = task.get_processing_time_details()
                    task_trace_queue.put(
                        (start, task_type, task_details, True, thread_name),
                    )
                    try:
                        task.execute()
                    except Exception as e:
                        end = time.time()
                        duration = end - start
                        result = ERRORED
                        logger.error(
                            f"executed task [failure]: {task_reference} failures: {e}"
                        )
                        try:
                            logger.error(f"---- START OF ERROR----")
                            logger.error(f"Task {task_type}:")
                            for l in serialisation_utils.dump(
                                unwrap(task_details)
                            ).split("\n"):
                                logger.error(l)
                            for l in traceback.format_exception(
                                etype=type(e), value=e, tb=e.__traceback__,
                            ):
                                for sl in l.split("\n"):
                                    logger.error(f"{sl}")
                            logger.error(f"---- END OF ERROR ----")
                        except Exception as e2:
                            logger.error(
                                f"Exception raised: {e2}  whilst logging exection: {e}"
                            )
                        task.on_task_failure(e, duration)
                    else:
                        end = time.time()
                        duration = end - start
                        result = COMPLETED
                        task.on_task_success(duration)

                    task_processing_time_queue.put(
                        (duration, task_type, task_details,),
                    )
                    task_trace_queue.put(
                        (end, task_type, task_details, False, thread_name),
                    )

                    # print(f"{pid} Worker {task_reference} waiting for lock to unlock resources", flush=True)
                    with lock:
                        logger.info(
                            f"executed task [success]: {task_reference} got lock to unlock resources"
                        )
                        unlock_resources_for_task(task_parameters, resources_file_path)
                        results_queue.put((task_reference, result))
                        time.sleep(0.1)
                else:
                    time.sleep(0.01)

        # time.sleep(10)
    logger.info(f"shutting down worker complete")


def scheduler_task(
    num_workers, task_queue, results_queue, control_queue, tasks_to_run,
):
    number_of_target_tasks_in_flight = num_workers
    should_be_running = True
    while should_be_running:
        dag = build_the_dag(tasks_to_run)
        generations = list(nx.topological_generations(dag))
        if not generations:
            logger.info("No more batches to run")
            control_queue.put(CONTROL_EVENT__COMPLETE)
            return

        current_generation = list(generations[-1])  # may need to make list
        number_of_tasks_in_flight = 0
        number_of_tasks_processed = 0
        number_of_tasks_in_generation = len(current_generation)
        current_generation_in_progress = True

        while current_generation_in_progress:
            logger.info("starting batch")
            # start each iteration by checking if the queue has enough jobs in it
            while (
                current_generation
                and number_of_tasks_in_flight < number_of_target_tasks_in_flight
            ):
                # there are enough jobs in the queue
                number_of_tasks_in_flight += 1
                task_to_run_reference = current_generation.pop()
                logger.info(f"sending: {task_to_run_reference}")
                task_queue.put(task_to_run_reference)
                time.sleep(1)

            # now handle a complete jobs from the workers
            task_reference, result = results_queue.get()
            if task_reference:
                number_of_tasks_in_flight -= 1
                number_of_tasks_processed += 1
                logger.info(
                    f"receiving: [{number_of_tasks_processed}]: {task_reference}, {result}"
                )
                tasks_to_run[task_reference][QUEUE_STATUS] = result

            if not current_generation:  # queue now empty - wait for all to complete
                logger.info("tasks now scheduled")
                while number_of_tasks_processed < number_of_tasks_in_generation:
                    task_reference, result = results_queue.get()
                    if task_reference:
                        number_of_tasks_in_flight -= 1
                        number_of_tasks_processed += 1
                        logger.info(
                            f"receiving: [{number_of_tasks_processed}]: {task_reference}, {result}"
                        )
                        tasks_to_run[task_reference][QUEUE_STATUS] = result
                else:
                    current_generation_in_progress = False
                    logger.info("finished batch")
    logger.info("finished all batches")


def run(
    num_workers,
    tasks_to_run,
    manifest_files_path,
    manifest_task_reference_file_path,
    puppet_account_id,
    execution_mode,
):
    logger.info(f"Running with {num_workers} processes in {execution_mode}!")

    resources_file_path = f"{manifest_files_path}/resources.json"
    start = time.time()
    os.environ["SCT_START_TIME"] = str(start)

    with open(resources_file_path, "w") as f:
        f.write("{}")

    QueueKlass = multiprocessing.Queue
    EventKlass = multiprocessing.Event
    ExecutorKlass = multiprocessing.Process
    LockKlass = multiprocessing.Lock

    lock = LockKlass()
    task_queue = QueueKlass()
    results_queue = QueueKlass()
    task_processing_time_queue = QueueKlass()
    task_trace_queue = QueueKlass()
    control_queue = QueueKlass()
    complete_event = EventKlass()

    worker_task_args = (
        lock,
        task_queue,
        results_queue,
        task_processing_time_queue,
        task_trace_queue,
        tasks_to_run,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
        resources_file_path,
    )
    scheduler_task_args = (
        num_workers,
        task_queue,
        results_queue,
        control_queue,
        tasks_to_run,
    )
    task_processing_time_args = (
        task_processing_time_queue,
        complete_event,
    )
    task_trace_args = (
        task_trace_queue,
        complete_event,
        puppet_account_id,
        execution_mode,
    )

    processes = [
        ExecutorKlass(
            name=f"worker#{i}", target=worker_task, args=(str(i),) + worker_task_args,
        )
        for i in range(num_workers)
    ]
    scheduler_thread = ExecutorKlass(
        name="scheduler", target=scheduler_task, args=scheduler_task_args,
    )
    on_task_processing_time_thread = ExecutorKlass(
        name="on_task_processing_time",
        target=task_processing_time.on_task_processing_time_task,
        args=task_processing_time_args,
    )
    on_task_trace_thread = ExecutorKlass(
        name="on_task_trace", target=task_trace.on_task_trace, args=task_trace_args,
    )

    on_task_processing_time_thread.start()
    on_task_trace_thread.start()
    for process in processes:
        process.start()
    scheduler_thread.start()
    while True:
        message = control_queue.get()
        if message == CONTROL_EVENT__COMPLETE:
            break
    for process in processes:
        process.terminate()
    time.sleep(10)
    on_task_processing_time_thread.terminate()
    on_task_trace_thread.terminate()
    logger.info(f"Time taken = {time.time() - start:.10f}")
