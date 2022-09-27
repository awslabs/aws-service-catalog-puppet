import multiprocessing
import time
import traceback

import networkx as nx
import json
from servicecatalog_puppet import constants

import os

from servicecatalog_puppet import print_utils
from servicecatalog_puppet.workflow.dependencies import task_factory
import pickle

TIMEOUT = 60 * 60

COMPLETED = "COMPLETED"
ERRORED = "ERRORED"
PENDING = "PENDING"
TRIGGER = "TRIGGER"
READY = "READY"
BLOCKED = "BLOCKED"

QUEUE_STATUS = "QUEUE_STATUS"


def get_next_task(pid, g, tasks_to_run_ref, resources_in_use):
    for node in g.nodes():
        if g.out_degree(node) == 0:
            next_task = tasks_to_run_ref.get(node)
            print(f"{pid} found a task: ", node)
            if next_task.get(QUEUE_STATUS, False) is False:
                print(f"{pid} found a task: ", node, " not running")
                can_run = True
                for r in next_task.get("resources_required", []):
                    if resources_in_use.get(r, False) is not False:
                        print(f"{pid} found a task: {node} which is blocked by task: {resources_in_use.get('r')}, using resource {r}")
                        can_run = False
                if can_run:
                    print(f"{pid} found a task: ", node, " and going to run it!")
                    return next_task
                else:
                    print(
                        f"{pid} Cannot schedule task {node} because of resources"
                    )
    return None


def build_initial_g(tasks_to_run):
    g = nx.DiGraph()
    for task in tasks_to_run:
        uid = task.get("task_reference")
        data = task
        g.add_nodes_from(
            [(uid, data), ]
        )
        for duid in task.get("dependencies_by_reference", []):
            g.add_edge(uid, duid)
    return g


def release_resources_for(pid, lock, task_parameters):
    with lock:
        with open(constants.RESOURCES, "r") as f:
            resources_in_use = json.load(f)
        for r in task_parameters.get("resources_required",  []):
            del resources_in_use[r]
        with open(constants.RESOURCES, "w") as f:
            json.dump(resources_in_use, f)


def get_a_task_to_run(pid, lock):
    with lock:
        print(f"{pid} AQUIRED")
        with open(constants.STATE_FILE_3, 'rb') as f:
            g = pickle.load(f)
        with open(constants.STATE_FILE_2, "r") as f:
            tasks_to_run_ref = json.loads(f.read()).get("all_tasks")
        with open(constants.RESOURCES, "r") as f:
            resources_in_use = json.loads(f.read())
        print(f"{pid} loaded files")

        task_parameters_to_try = get_next_task(pid, g, tasks_to_run_ref, resources_in_use)
        while task_parameters_to_try is not None:
            print(f"{pid} got task_parameters")
            if task_parameters_to_try:
                task_reference = task_parameters_to_try.get("task_reference")
                for r in task_parameters_to_try.get("resources_required", []):
                    resources_in_use[r] = task_reference
                tasks_to_run_ref[task_reference][QUEUE_STATUS] = PENDING
                with open(constants.STATE_FILE_2, "w") as f:
                    f.write(
                        json.dumps(dict(all_tasks=tasks_to_run_ref))
                    )
                with open(constants.RESOURCES, "w") as f:
                    f.write(
                        json.dumps(resources_in_use)
                    )
                return task_parameters_to_try
            time.sleep(0.5)
            task_parameters_to_try = get_next_task(pid, g, tasks_to_run_ref, resources_in_use)
    return None


def worker_task(
        lock,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
):
    pid = os.getpid()
    print_utils.echo(f"{pid} Worker starting up")
    while True:
        print(f"{pid} about to acquire", flush=True)
        task_parameters = get_a_task_to_run(pid, lock)
        print(f"{pid} end of acquire", flush=True)
        if task_parameters is None:
            time.sleep(0.25)
            continue

        task = task_factory.create(
            manifest_files_path=manifest_files_path,
            manifest_task_reference_file_path=manifest_task_reference_file_path,
            puppet_account_id=puppet_account_id,
            parameters_to_use=task_parameters,
        )
        task_reference = task.task_reference
        print_utils.echo(f"{pid} Worker executing task: {task_reference}")
        task.on_task_start()
        start = time.time()
        try:
            task.run()
            end = time.time()
        except Exception as e:
            print_utils.error(
                f"{pid} Worker executed task with failures: {task_reference} failures: {e}"
            )
            print_utils.error("---- START OF ERROR----")
            for l in traceback.format_exception(
                    etype=type(e), value=e, tb=e.__traceback__,
            ):
                print_utils.error(l)
            print_utils.error("---- END OF ERROR ----")
            task.on_task_failure(e)
        else:
            print_utils.echo(f"{pid} Worker executed task: {task_reference}")
            task.on_task_success()
            task.on_task_processing_time(int(end - start))
            print_utils.echo(f"{pid} Worker reported task complete: {task_reference}")
        release_resources_for(pid, lock, task_parameters)

        time.sleep(10)
    print_utils.echo(f"{pid} Worker shutting down")


def remove_task_from_graph(g, task_just_run):
    g.remove_node(task_just_run)


def run(
        num_workers,
        tasks_to_run,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
):
    num_workers = 50

    print_utils.echo(f"Running with {num_workers} processes!")
    start = time.time()
    multiprocessing.set_start_method("forkserver")
    lock = multiprocessing.Lock()

    g = build_initial_g(tasks_to_run)
    with open(constants.STATE_FILE_3, 'wb') as f:
        pickle.dump(g, f)
    with open(constants.RESOURCES, 'w') as f:
        f.write(
            "{}"
        )

    processes = [
        multiprocessing.Process(
            target=worker_task,
            args=(
                lock,
                manifest_files_path,
                manifest_task_reference_file_path,
                puppet_account_id,
            ),
        )
        for _ in range(num_workers)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    print_utils.echo(f"Time taken = {time.time() - start:.10f}")
