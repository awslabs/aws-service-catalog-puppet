#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import queue
import time
import traceback

from servicecatalog_puppet import serialisation_utils
from servicecatalog_puppet.serialisation_utils import unwrap
from servicecatalog_puppet.waluigi.constants import COMPLETED, ERRORED
from servicecatalog_puppet.waluigi.dag_utils import logger
from servicecatalog_puppet.waluigi.locks.external import (
    are_resources_are_free_for_task,
    lock_resources_for_task,
    unlock_resources_for_task,
)
from servicecatalog_puppet.workflow.dependencies import task_factory


def worker_task(
    thread_name,
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
):
    logger.info(f"starting up")
    should_be_running = True
    if control_event:
        should_be_running = not control_event.is_set()
    while should_be_running:
        if control_event:
            time.sleep(0.1)
        try:
            task_reference = task_queue.get(timeout=5)
        except queue.Empty:
            if control_event:
                should_be_running = not control_event.is_set()
            continue
        else:
            result = False
            while not result:
                # print(
                #     f"{pid} Worker received {task_reference} waiting for lock",
                #     flush=True,
                # )
                task_parameters = all_tasks.get(task_reference)
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
        if control_event:
            should_be_running = not control_event.is_set()
    logger.info(f"shutting down")
