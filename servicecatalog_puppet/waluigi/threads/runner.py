#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import queue
import threading
import time

from servicecatalog_puppet.waluigi.dag_utils import (
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


QUEUE_REFILL_SLEEP_DURATION = 0.2


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
        f"Running with {make_readable_in_codebuild_logs(num_workers)} threads in {execution_mode} with scheduling_algorithm {scheduling_algorithm}!"
    )

    all_tasks = tasks_reference
    resources = dict()
    tasks_to_run = list()

    resources_file_path = f"{manifest_files_path}/resources.json"
    start = time.time()
    os.environ["SCT_START_TIME"] = str(start)

    with open(resources_file_path, "w") as f:
        f.write("{}")

    QueueKlass = queue.Queue
    EventKlass = threading.Event
    ExecutorKlass = threading.Thread
    LockKlass = threading.Lock

    lock = LockKlass()
    task_queue = QueueKlass()
    control_queue = None
    results_queue = QueueKlass()
    task_processing_time_queue = QueueKlass()
    task_trace_queue = QueueKlass()
    control_event = EventKlass()
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
    if scheduler_task_to_use:
        scheduler_thread.start()
    while not control_event.is_set():
        time.sleep(5)
    for process in processes:
        process.join(timeout=1)
    time.sleep(10)
    complete_event.set()
    logger.info(f"Time taken = {time.time() - start:.10f}")
