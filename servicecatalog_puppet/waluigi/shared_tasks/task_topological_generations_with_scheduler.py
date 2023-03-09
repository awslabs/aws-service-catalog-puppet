#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import time

import networkx as nx

from servicecatalog_puppet.waluigi.constants import (
    CONTROL_EVENT__COMPLETE,
    QUEUE_STATUS,
)
from servicecatalog_puppet.waluigi.dag_utils import build_the_dag, logger


def scheduler_task(
    num_workers,
    task_queue,
    results_queue,
    control_queue,
    control_event,
    queue_refill_sleep_duration,
    all_tasks,
    tasks_to_run,
):
    number_of_target_tasks_in_flight = num_workers
    should_be_running = True
    if control_event:
        should_be_running = not control_event.is_set()
    while should_be_running:
        dag = build_the_dag(all_tasks)
        generations = list(nx.topological_generations(dag))
        if not generations:
            logger.info("No more batches to run")
            if control_queue:
                control_queue.put(CONTROL_EVENT__COMPLETE)
            if control_event:
                control_event.set()
            return

        current_generation = list(generations[-1])
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
                time.sleep(queue_refill_sleep_duration)

            # now handle a complete jobs from the workers
            task_reference, result = results_queue.get()
            if task_reference:
                number_of_tasks_in_flight -= 1
                number_of_tasks_processed += 1
                logger.info(
                    f"receiving: [{number_of_tasks_processed}]: {task_reference}, {result}"
                )
                task_just_run = all_tasks[task_reference]
                task_just_run[QUEUE_STATUS] = result
                all_tasks[task_reference] = task_just_run

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
                        task_just_run = all_tasks[task_reference]
                        task_just_run[QUEUE_STATUS] = result
                        all_tasks[task_reference] = task_just_run
                else:
                    current_generation_in_progress = False
                    logger.info("finished batch")
        if control_event:
            should_be_running = not control_event.is_set()
    logger.info("finished all batches")
