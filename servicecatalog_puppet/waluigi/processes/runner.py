import multiprocessing
import os
import time

from servicecatalog_puppet.waluigi.constants import (
    CONTROL_EVENT__COMPLETE,
)
from servicecatalog_puppet.waluigi.dag_utils import logger
from servicecatalog_puppet.waluigi.shared_tasks import task_processing_time
from servicecatalog_puppet.waluigi.shared_tasks import task_trace
from servicecatalog_puppet.waluigi.shared_tasks.task_topological_generations_with_scheduler import scheduler_task
from servicecatalog_puppet.waluigi.shared_tasks.workers.worker_requiring_scheduler import worker_task

QUEUE_REFILL_SLEEP_DURATION = 1

def get_tasks(scheduling_algorithm):
    if scheduling_algorithm == "topological_generations":
        return worker_task, scheduler_task
    raise ValueError(f"Unsupported scheduling_algorithm: {scheduling_algorithm}")


def run(
    num_workers,
    tasks_to_run,
    manifest_files_path,
    manifest_task_reference_file_path,
    puppet_account_id,
    execution_mode,
    scheduling_algorithm,
):
    logger.info(f"Running with {range(500)[num_workers]} processes in {execution_mode} with scheduling_algorithm {scheduling_algorithm}!")

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
    control_event = None
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
        control_event,
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
        control_event,
        QUEUE_REFILL_SLEEP_DURATION,
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

    worker_task_to_use, scheduler_task_to_use = get_tasks(scheduling_algorithm)

    processes = [
        ExecutorKlass(
            name=f"worker#{i}", target=worker_task_to_use, args=(str(i),) + worker_task_args,
        )
        for i in range(num_workers)
    ]
    scheduler_thread = None
    if scheduler_task:
        scheduler_thread = ExecutorKlass(
            name="scheduler", target=scheduler_task_to_use, args=scheduler_task_args,
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
    if scheduler_thread:
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
