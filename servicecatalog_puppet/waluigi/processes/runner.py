#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import multiprocessing
import os
import time

import networkx as nx

from servicecatalog_puppet.waluigi.constants import CONTROL_EVENT__COMPLETE
from servicecatalog_puppet.waluigi.dag_utils import (
    build_the_dag,
    logger,
    make_readable_in_codebuild_logs,
)
from servicecatalog_puppet.waluigi.shared_tasks import (
    task_processing_time,
    task_topological_generations_with_scheduler,
    task_topological_generations_without_scheduler,
    task_trace,
)
from servicecatalog_puppet.waluigi.shared_tasks.workers import (
    worker_requiring_scheduler,
)


QUEUE_REFILL_SLEEP_DURATION = 1


def get_tasks(scheduling_algorithm):
    if scheduling_algorithm == "topological_generations":
        return (
            worker_requiring_scheduler.worker_task,
            task_topological_generations_with_scheduler.scheduler_task,
        )
    if scheduling_algorithm == "topological_generations_without_scheduler":
        return task_topological_generations_without_scheduler.worker_task, None
    raise ValueError(f"Unsupported scheduling_algorithm: {scheduling_algorithm}")


def run(
    num_workers,
    tasks_reference,
    manifest_files_path,
    manifest_task_reference_file_path,
    puppet_account_id,
    execution_mode,
    scheduling_algorithm,
):
    logger.info(
        f"Executing {len(tasks_reference.keys())} tasks with {make_readable_in_codebuild_logs(num_workers)} processes in {execution_mode} with scheduling_algorithm {scheduling_algorithm}!"
    )

    manager = multiprocessing.Manager()
    all_tasks = manager.dict(tasks_reference)
    resources = manager.dict()
    tasks_to_run = manager.list()

    dag = build_the_dag(tasks_reference)
    generations = list(nx.topological_generations(dag))
    if not generations:
        raise ValueError("No tasks to run")
    while generations:
        tasks_to_run.extend(list(generations.pop()))

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
        control_queue,
        control_event,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
        resources_file_path,
        all_tasks,
        resources,
        tasks_to_run,
    )
    scheduler_task_args = (
        num_workers,
        task_queue,
        results_queue,
        control_queue,
        control_event,
        QUEUE_REFILL_SLEEP_DURATION,
        all_tasks,
        tasks_to_run,
    )
    task_processing_time_args = (
        task_processing_time_queue,
        complete_event,
        execution_mode,
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
            name=f"worker#{i}",
            target=worker_task_to_use,
            args=(str(i),) + worker_task_args,
        )
        for i in range(num_workers)
    ]
    scheduler_thread = None

    if scheduler_task_to_use:
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
        logger.info("Waiting for shutdown message")
        message = control_queue.get()
        if message == CONTROL_EVENT__COMPLETE:
            logger.info(f"Got the {message}, starting shutdown process")
            break

    for process in processes:
        process.terminate()
    time.sleep(10)
    on_task_processing_time_thread.terminate()
    on_task_trace_thread.terminate()
    logger.info(f"Time taken = {time.time() - start:.10f}")
