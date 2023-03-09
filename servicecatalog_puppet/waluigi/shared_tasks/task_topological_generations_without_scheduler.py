#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import time
import traceback

from servicecatalog_puppet import serialisation_utils
from servicecatalog_puppet.serialisation_utils import unwrap
from servicecatalog_puppet.waluigi.constants import (
    BLOCKED,
    COMPLETED,
    CONTROL_EVENT__COMPLETE,
    ERRORED,
    IN_PROGRESS,
    NOT_SET,
    QUEUE_STATUS,
    RESOURCES_REQUIRED,
)
from servicecatalog_puppet.waluigi.dag_utils import logger
from servicecatalog_puppet.waluigi.locks.external import (
    are_resources_are_free_for_task_dict,
)
from servicecatalog_puppet.workflow.dependencies import task_factory


def has_dependencies_remaining(task_to_run, all_tasks):
    is_currently_blocked = False
    is_permanently_blocked = False
    for dependency in task_to_run.get("dependencies_by_reference"):
        if all_tasks.get(dependency):
            dependency_status = all_tasks[dependency].get(QUEUE_STATUS, NOT_SET)
            if dependency_status in [ERRORED, BLOCKED]:
                is_currently_blocked = is_permanently_blocked = True
                return is_currently_blocked, is_permanently_blocked
            else:
                if dependency_status != COMPLETED:
                    is_currently_blocked = True
                    return is_currently_blocked, is_permanently_blocked
    return is_currently_blocked, is_permanently_blocked


def get_next_task_to_run(tasks_to_run, resources, all_tasks):
    task_permanently_blocked_status = list()
    for task_reference_to_run in tasks_to_run:
        task_to_run = all_tasks[task_reference_to_run]
        status = task_to_run.get(QUEUE_STATUS, NOT_SET)
        # check if not running or has previously run
        if status == IN_PROGRESS:
            task_permanently_blocked_status.append(False)
        elif status == NOT_SET:
            is_currently_blocked, is_permanently_blocked = has_dependencies_remaining(
                task_to_run, all_tasks
            )
            if is_permanently_blocked:
                task_to_run[QUEUE_STATUS] = BLOCKED
                all_tasks[task_reference_to_run] = task_to_run
            task_permanently_blocked_status.append(is_permanently_blocked)
            if not is_currently_blocked:
                are_resources_are_free, _ = are_resources_are_free_for_task_dict(
                    task_to_run, resources
                )
                if are_resources_are_free:
                    return task_to_run, False
    return None, all(task_permanently_blocked_status)


def lock_next_task_to_run(next_task, resources, all_tasks):
    task_reference = next_task["task_reference"]
    next_task[QUEUE_STATUS] = IN_PROGRESS
    all_tasks[task_reference] = next_task
    for r in next_task.get(RESOURCES_REQUIRED, []):
        resources[r] = task_reference


def setup_next_task_to_run(lock, tasks_to_run, resources, all_tasks):
    with lock:
        next_task, can_shut_down = get_next_task_to_run(
            tasks_to_run, resources, all_tasks
        )
        if next_task is not None:
            lock_next_task_to_run(next_task, resources, all_tasks)
    return next_task, can_shut_down


def set_task_as_run(lock, next_task, all_tasks, resources, result):
    with lock:
        for r in next_task.get(RESOURCES_REQUIRED, []):
            try:
                del resources[r]
            except KeyError:
                logger.warn(
                    f"{next_task.get('task_reference')} tried to unlock {r} but it wasn't present"
                )
        next_task[QUEUE_STATUS] = result
        all_tasks[next_task["task_reference"]] = next_task


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
    should_run = True

    while should_run:
        next_task = None
        while next_task is None:
            next_task, can_shut_down = setup_next_task_to_run(
                lock, tasks_to_run, resources, all_tasks
            )
            if can_shut_down:
                if control_queue:
                    control_queue.put(CONTROL_EVENT__COMPLETE)
                if control_event:
                    control_event.set()
                return
            time.sleep(1)

        task_reference = next_task["task_reference"]
        task = task_factory.create(
            manifest_files_path=manifest_files_path,
            manifest_task_reference_file_path=manifest_task_reference_file_path,
            puppet_account_id=puppet_account_id,
            parameters_to_use=next_task,
        )
        logger.info(f"executing task: {task_reference}")
        task.on_task_start()
        start = time.time()
        task_type, task_details = task.get_processing_time_details()
        task_trace_queue.put((start, task_type, task_details, True, thread_name),)
        try:
            task.execute()
        except Exception as e:
            end = time.time()
            duration = end - start
            result = ERRORED
            logger.error(f"executed task [failure]: {task_reference} failures: {e}")
            try:
                logger.error(f"---- START OF ERROR----")
                logger.error(f"Task {task_type}:")
                for l in serialisation_utils.dump(unwrap(task_details)).split("\n"):
                    logger.error(l)
                for l in traceback.format_exception(
                    etype=type(e), value=e, tb=e.__traceback__,
                ):
                    for sl in l.split("\n"):
                        logger.error(f"{sl}")
                logger.error(f"---- END OF ERROR ----")
            except Exception as e2:
                logger.error(f"Exception raised: {e2}  whilst logging exection: {e}")
            task.on_task_failure(e, duration)
        else:
            end = time.time()
            duration = end - start
            result = COMPLETED
            logger.info(f"executed task [{result}]: {task_reference}")
            task.on_task_success(duration)

        task_processing_time_queue.put((duration, task_type, task_details,),)
        task_trace_queue.put((end, task_type, task_details, False, thread_name),)

        # print(f"{pid} Worker {task_reference} waiting for lock to unlock resources", flush=True)
        logger.info(f"executed task [success]: {task_reference}")
        set_task_as_run(lock, next_task, all_tasks, resources, result)
        time.sleep(0.01)

    logger.info(f"shutting down")
