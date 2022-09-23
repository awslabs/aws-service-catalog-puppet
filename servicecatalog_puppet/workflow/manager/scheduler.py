import multiprocessing
import time

import networkx as nx
import json
from servicecatalog_puppet import constants

import os

from servicecatalog_puppet.commands import graph
from servicecatalog_puppet.workflow.dependencies import get_dependencies_for_task_reference

TIMEOUT = 60 * 60


QUEUE_STATUS = "QUEUE_STATUS"


def build_ordered_tasks_from_dag(tasks_to_run):
    g = nx.DiGraph()
    for task in tasks_to_run:
        uid = task.get("task_reference")
        data = task
        g.add_nodes_from(
            [(uid, data), ]
        )
        for duid in task.get("dependencies_by_reference", []):
            g.add_edge(uid, duid)
    result = list(nx.topological_sort(g))
    result.reverse()
    return result


def process_task(input_tasks, output_tasks):
    pid = os.getpid()
    print(f"{pid} process_task in", flush=True)
    while True:
        task = input_tasks.get()
        if task is None:
            time.sleep(.01)
            continue
        print(f"{pid} is running {task.task_reference}", flush=True)
        time.sleep(0.1)
        output_tasks.put(task.task_reference)
        print(f"{pid} process_task put", flush=True)
    print(f"{pid} process_task out", flush=True)


def get_next_tasks_to_run_for_task(task_to_maybe_run, tasks_in_order, tasks_to_run):
    for d_reference in task_to_maybe_run.get("dependencies_by_reference"):
        d = tasks_to_run.get(d_reference)
        if d.get(QUEUE_STATUS, False) is False:
            sub_d = get_next_tasks_to_run_for_task(d, tasks_in_order, tasks_to_run)
            if sub_d is None:
                return d
            else:
                return sub_d
    return None


def get_next_task_to_run(tasks_in_order, tasks_to_run):
    for task_to_maybe_run_reference in tasks_in_order:
        task_to_maybe_run = tasks_to_run.get(task_to_maybe_run_reference)
        if task_to_maybe_run.get(QUEUE_STATUS, False) is False:
            dependent_task_to_maybe_run = get_next_tasks_to_run_for_task(task_to_maybe_run, tasks_in_order, tasks_to_run)
            if dependent_task_to_maybe_run is None:
                return task_to_maybe_run
            else:
                return dependent_task_to_maybe_run
    return None


def orchestrate(input_tasks, output_task):
    pid = os.getpid()
    print(f"{pid} orchestrate in", flush=True)
    with open(constants.STATE_FILE_1, 'r') as f:
        tasks_in_order = json.loads(
            f.read()
        )
    n_tasks_to_run = len(tasks_in_order)
    tasks_queued_so_far = 0
    tasks_completed_so_far = 0
    with open(constants.STATE_FILE_2, 'r') as f:
        tasks_to_run = json.loads(
            f.read()
        )
        tasks_to_run = tasks_to_run.get("all_tasks")
    while True:
        task = output_task.get()
        if task is None:
            time.sleep(1)
            continue

        if task != "trigger":
            tasks_completed_so_far += 1
            tasks_to_run[task][QUEUE_STATUS] = "COMPLETED"

        task_to_run_next = get_next_task_to_run(tasks_in_order, tasks_to_run)
        if task_to_run_next:
            puppet_account_id = "105463962595"
            f = "ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml"
            path = "ignored/src/ServiceCatalogPuppet"
            tasks_to_run[task_to_run_next.get("task_reference")][QUEUE_STATUS] = "PENDING"
            print(f"{pid} orchestrate adding {task_to_run_next.get('task_reference')}", flush=True)
            tasks_queued_so_far += 1
            input_tasks.put(
                get_dependencies_for_task_reference.create(
                    manifest_files_path=path,
                    manifest_task_reference_file_path=f,
                    puppet_account_id=puppet_account_id,
                    parameters_to_use=task_to_run_next
                )
            )
            print(f"{pid} orchestrate put", flush=True)
        else:
            time.sleep(1)
        print(f"tasks complete: {tasks_completed_so_far}, queued: {tasks_queued_so_far}, total: {n_tasks_to_run}")


def run(num_workers, tasks_to_run):
    num_workers = 20
    tasks_in_order = build_ordered_tasks_from_dag(
        tasks_to_run
    )
    with open(constants.STATE_FILE_1, 'w') as f:
        f.write(
            json.dumps(
                tasks_in_order
            )
        )
    with open(constants.STATE_FILE_2, 'r') as f:
        tasks_to_run = json.loads(
            f.read()
        )
        tasks_to_run = tasks_to_run.get("all_tasks")

    print(f"Running with {num_workers} processes!", flush=True)
    # assume first task has no dependencies otherwise DAG is not a DAG
    start = time.time()
    multiprocessing.set_start_method('forkserver')
    input_tasks = multiprocessing.JoinableQueue()
    output_tasks = multiprocessing.Queue()
    for i in range(num_workers):
        output_tasks.put("trigger")
    processes = [multiprocessing.Process(target=process_task, args=(input_tasks, output_tasks)) for i in
                 range(num_workers)]
    processes.append(
        multiprocessing.Process(
            target=orchestrate,
            args=(input_tasks, output_tasks),
        )
    )
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    print(f"Time taken = {time.time() - start:.10f}", flush=True)
