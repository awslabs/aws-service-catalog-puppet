import multiprocessing
import random
import time
import traceback

import networkx as nx
import json
from servicecatalog_puppet import constants

import os

from servicecatalog_puppet import print_utils
from servicecatalog_puppet.workflow.dependencies import task_factory

TIMEOUT = 60 * 60

COMPLETED = "COMPLETED"
ERRORED = "ERRORED"
PENDING = "PENDING"
TRIGGER = "TRIGGER"
READY = "READY"
BLOCKED = "BLOCKED"

QUEUE_STATUS = "QUEUE_STATUS"


def build_ordered_tasks_from_dag(tasks_to_run):
    g = nx.DiGraph()
    for task in tasks_to_run:
        uid = task.get("task_reference")
        data = task
        g.add_nodes_from(
            [(uid, data),]
        )
        for duid in task.get("dependencies_by_reference", []):
            g.add_edge(uid, duid)
    result = list(nx.topological_sort(g))
    result.reverse()
    return result


def worker_task(
    input_tasks,
    output_tasks,
    manifest_files_path,
    manifest_task_reference_file_path,
    puppet_account_id,
):
    pid = os.getpid()
    print_utils.echo(f"{pid} Worker starting up")
    while True:
        task = input_tasks.get()
        if task is None:
            time.sleep(0.25)
            continue
        task_reference = task.task_reference
        print_utils.echo(f"{pid} Worker executing task: {task_reference}")
        task.on_task_start()
        start = time.time()
        try:
            task.run()
            end = time.time()
        except Exception as e:
            print_utils.error(f"{pid} Worker executed task with failures: {task_reference} failures: {e}")
            print_utils.error('---- START OF ERROR----')
            for l in traceback.format_exception(
                    etype=type(e), value=e, tb=e.__traceback__,
                ):
                    print_utils.error(
                        l
                    )
            print_utils.error('---- END OF ERROR ----')
            task.on_task_failure(e)
            output_tasks.put((ERRORED, task_reference,))
        else:
            print_utils.echo(f"{pid} Worker executed task: {task_reference}")
            task.on_task_success()
            task.on_task_processing_time(int(end - start))
            output_tasks.put((COMPLETED, task_reference,))
    print_utils.echo(f"{pid} Worker shutting down")


def get_next_tasks_to_run_for_task(
    task_to_maybe_run, tasks_in_order, tasks_to_run, resources_in_use
):
    num_of_children_complete = 0
    is_blocked = False
    for d_reference in task_to_maybe_run.get("dependencies_by_reference"):
        d = tasks_to_run.get(d_reference)
        d_status = d.get(QUEUE_STATUS, False)
        if d_status == COMPLETED:
            num_of_children_complete += 1
            continue
        elif d_status == ERRORED:
            is_blocked = True
        elif d_status == PENDING:
            continue
        else:
            # TASK NOT PENDING OR RUNNING BUT CHILDREN UNKNOWN
            next_child = get_next_tasks_to_run_for_task(
                d, tasks_in_order, tasks_to_run, resources_in_use
            )
            if next_child is not None:
                return next_child
    # children were not returned and so want to check task_to_maybe_run as all children should be complete by now
    if is_blocked:
        task_to_maybe_run[QUEUE_STATUS] = BLOCKED
        return None

    if num_of_children_complete == len(task_to_maybe_run.get("dependencies_by_reference")):
        status = task_to_maybe_run.get(QUEUE_STATUS, False)
        if status is False:
            for r in task_to_maybe_run.get("resources_required", []):
                if resources_in_use.get(r):
                    print_utils.echo(
                        f"Orchestrator not executing task: {task_to_maybe_run.get('task_reference')}, another task has already reserved the resource: {r}"
                    )
                    return None
            return task_to_maybe_run
        else:
            return None

    else:
        return None


def get_next_task_to_run(tasks_in_order, tasks_to_run, resources_in_use):
    for task_to_maybe_run_reference in tasks_in_order:
        task_to_maybe_run = tasks_to_run.get(task_to_maybe_run_reference)
        status = task_to_maybe_run.get(QUEUE_STATUS, False)
        if status == READY:
            return task_to_maybe_run
        elif status is False:  # is not pending or complete or errored
            # check children first
            dependent_task_to_maybe_run = get_next_tasks_to_run_for_task(
                task_to_maybe_run, tasks_in_order, tasks_to_run, resources_in_use
            )
            if dependent_task_to_maybe_run is not None:
                return dependent_task_to_maybe_run
    return None


def orchestrate(input_tasks, output_task):
    pid = os.getpid()
    print_utils.echo(f"{pid} orchestrate in")
    resources_in_use = dict()
    with open(constants.STATE_FILE_1, "r") as f:
        tasks_in_order = json.loads(f.read())
    n_tasks_to_run = len(tasks_in_order)
    tasks_errored = 0
    tasks_queued_so_far = 0
    tasks_completed_so_far = 0
    with open(constants.STATE_FILE_2, "r") as f:
        tasks_to_run = json.loads(f.read())
        tasks_to_run = tasks_to_run.get("all_tasks")
    # START ORCHESTRATING
    while True:
        result, task = output_task.get()

        if result != TRIGGER:
            tasks_completed_so_far += 1
            task_just_run = tasks_to_run[task]

            if result == COMPLETED:
                task_just_run[QUEUE_STATUS] = COMPLETED
                for r in task_just_run.get("resources_required", []):
                    resources_in_use[r] = False
            elif result == ERRORED:
                tasks_errored += 1
                time.sleep(2)
                task_just_run[QUEUE_STATUS] = ERRORED
                for r in task_just_run.get("resources_required", []):
                    resources_in_use[r] = False
                time.sleep(2)

        task_to_run_next = get_next_task_to_run(
            tasks_in_order, tasks_to_run, resources_in_use
        )
        if task_to_run_next:
            for r in task_to_run_next.get("resources_required", []):
                resources_in_use[r] = True

            puppet_account_id = "105463962595"
            f = "ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml"
            path = "ignored/src/ServiceCatalogPuppet"
            tasks_to_run[task_to_run_next.get("task_reference")][QUEUE_STATUS] = PENDING
            print_utils.echo(
                f"{pid} Scheduling task: {task_to_run_next.get('task_reference')}",
            )
            tasks_queued_so_far += 1
            input_tasks.put(
                task_factory.create(
                    manifest_files_path=path,
                    manifest_task_reference_file_path=f,
                    puppet_account_id=puppet_account_id,
                    parameters_to_use=task_to_run_next,
                )
            )
        else:
            print_utils.echo(f"{pid} Not scheduling anything for now",)
            time.sleep(1)
        print_utils.echo(
            f"tasks complete: {tasks_completed_so_far}, errored: {tasks_errored}, queued: {tasks_queued_so_far}, total: {n_tasks_to_run}",
        )


def run(
    num_workers,
    tasks_to_run,
    manifest_files_path,
    manifest_task_reference_file_path,
    puppet_account_id,
):
    num_workers = 60
    tasks_in_order = build_ordered_tasks_from_dag(tasks_to_run)
    with open(constants.STATE_FILE_1, "w") as f:
        f.write(json.dumps(tasks_in_order))

    print_utils.echo(f"Running with {num_workers} processes!")
    start = time.time()
    multiprocessing.set_start_method("forkserver")
    input_tasks = multiprocessing.JoinableQueue()
    output_tasks = multiprocessing.Queue()
    for i in range(num_workers):
        output_tasks.put((TRIGGER, None))
    processes = [
        multiprocessing.Process(
            target=worker_task,
            args=(
                input_tasks,
                output_tasks,
                manifest_files_path,
                manifest_task_reference_file_path,
                puppet_account_id,
            ),
        )
        for _ in range(num_workers)
    ]
    processes.append(
        multiprocessing.Process(target=orchestrate, args=(input_tasks, output_tasks),)
    )
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    print_utils.echo(f"Time taken = {time.time() - start:.10f}")
