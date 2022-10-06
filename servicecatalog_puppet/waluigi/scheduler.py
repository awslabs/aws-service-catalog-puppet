import multiprocessing
import time
import traceback

import networkx as nx

# from viztracer import get_tracer, VizTracer

from servicecatalog_puppet import constants, serialisation_utils

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

RESOURCES_REQUIRED = "resources_required"


def build_the_dag(tasks_to_run):
    g = nx.DiGraph()
    for uid, task in tasks_to_run.items():
        data = task
        g.add_nodes_from(
            [(uid, data), ]
        )
        for duid in task.get("dependencies_by_reference", []):
            g.add_edge(uid, duid)
    return g


def are_resources_are_free_for_task(task_parameters, resources_file_path):
    with open(resources_file_path, "rb") as f:
        resources_in_use = serialisation_utils.json_loads(f.read())
    return (
        all(
            resources_in_use.get(r, False) is False
            for r in task_parameters.get(RESOURCES_REQUIRED, [])
        ),
        resources_in_use,
    )


def lock_resources_for_task(task_reference, task_parameters, resources_in_use, resources_file_path):
    print(f"Worker locking {task_reference}")
    for r in task_parameters.get(RESOURCES_REQUIRED, []):
        resources_in_use[r] = task_reference
    with open(resources_file_path, "wb") as f:
        f.write(serialisation_utils.json_dumps(resources_in_use))


def unlock_resources_for_task(task_parameters, resources_file_path):
    with open(resources_file_path, "rb") as f:
        resources_in_use = serialisation_utils.json_loads(f.read())
    for r in task_parameters.get(RESOURCES_REQUIRED, []):
        try:
            del resources_in_use[r]
        except KeyError:
            print_utils.warn(f"{task_parameters.get('task_reference')} tried to unlock {r} but it wasn't present")
    with open(resources_file_path, "wb") as f:
        f.write(serialisation_utils.json_dumps(resources_in_use))


def worker_task(
        lock,
        task_queue,
        results_queue,
        tasks_to_run,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
        resources_file_path,
):
    pid = os.getpid()

    # tracer = VizTracer(**init_kwargs)
    # tracer.register_exit()
    # tracer.start()

    print_utils.echo(f"{pid} Worker starting up")
    while True:
        task_reference = task_queue.get()
        if task_reference:
            result = False
            while not result:
                # print(f"{pid} Worker received {task_reference} waiting for lock", flush=True)
                task_parameters = tasks_to_run.get(task_reference)

                with lock:
                    # print(f"{pid} Worker {task_reference} got the lock", flush=True)
                    (
                        resources_are_free,
                        resources_in_use,
                    ) = are_resources_are_free_for_task(task_parameters, resources_file_path)
                    # print(f"{pid} Worker {task_reference} resources_are_free: {resources_are_free}", flush=True)
                    if resources_are_free:
                        lock_resources_for_task(
                            task_reference, task_parameters, resources_in_use, resources_file_path
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
                    print_utils.echo(f"{pid} Worker executing task: {task_reference}")
                    task.on_task_start()
                    start = time.time()
                    try:
                        task.run()
                        end = time.time()
                    except Exception as e:
                        result = ERRORED
                        print_utils.error(
                            f"{pid} Worker executed task [failure]: {task_reference} failures: {e}"
                        )
                        print_utils.error("---- START OF ERROR----")
                        for l in traceback.format_exception(
                                etype=type(e), value=e, tb=e.__traceback__,
                        ):
                            print_utils.error(l)
                        print_utils.error("---- END OF ERROR ----")
                        task.on_task_failure(e)
                    else:
                        result = COMPLETED
                        task.on_task_success()
                        task.on_task_processing_time(int(end - start))

                    # print(f"{pid} Worker {task_reference} waiting for lock to unlock resources", flush=True)
                    with lock:
                        print_utils.echo(
                            f"{pid} Worker executed task [success]: {task_reference} got lock to unlock resources")
                        unlock_resources_for_task(task_parameters, resources_file_path)
                        results_queue.put((task_reference, result))
                else:
                    time.sleep(0.01)

        # time.sleep(10)
    print_utils.echo(f"{pid} Worker shutting down")


def scheduler(
        num_workers,
        task_queue,
        results_queue,
        tasks_to_run,
        resources_in_use,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
):
    number_of_target_tasks_in_flight = num_workers
    workers_are_needed = True
    dag = build_the_dag(tasks_to_run)
    while workers_are_needed:
        print("the top loop")
        generations = list(nx.topological_generations(dag))
        if not generations:
            workers_are_needed = False
            continue

        current_generation = list(generations[-1]) # may need to make list
        number_of_tasks_in_flight = 0
        number_of_tasks_processed = 0
        number_of_tasks_in_generation = len(current_generation)
        current_generation_in_progress = True

        while current_generation_in_progress:
            print("Starting a new generation", flush=True)
            # start each iteration by checking if the queue has enough jobs in it
            while current_generation and number_of_tasks_in_flight < number_of_target_tasks_in_flight:
                print("generation has tasks and not enough tasks in flight", flush=True)
                # there are enough jobs in the queue
                number_of_tasks_in_flight += 1
                task_to_run_reference = current_generation.pop()
                print_utils.echo(f"scheduler sending: {task_to_run_reference}")
                task_queue.put(task_to_run_reference)

            print("consuming tasks from workers now", flush=True)
            # now handle a complete jobs from the workers
            task_reference, result = results_queue.get()
            if task_reference:
                number_of_tasks_in_flight -= 1
                print_utils.echo(f"scheduler receiving: {task_reference}, {result}")
                number_of_tasks_processed += 1

                if result == COMPLETED:
                    # print(f"scheduler removing {task_reference} from the dag")
                    dag.remove_node(task_reference)
                elif result == ERRORED:
                    # need to remove node and all paths depending on it
                    # also need to record that is was removed
                    pass

            if not current_generation: # queue now empty - wait for all to complete
                print("all tasks have been queued", flush=True)
                while number_of_tasks_processed < number_of_tasks_in_generation:
                    print("need to wait for another task to finish", flush=True)
                    task_reference, result = results_queue.get()
                    if task_reference:
                        number_of_tasks_in_flight -= 1
                        print_utils.echo(f"scheduler receiving: {task_reference}, {result}")
                        number_of_tasks_processed += 1
                else:
                    current_generation_in_progress = False
                    print("finished waiting for all tasks in current generation", flush=True)


def run(
        num_workers,
        tasks_to_run,
        manifest_files_path,
        manifest_task_reference_file_path,
        puppet_account_id,
):
    resources_file_path = f"{manifest_files_path}/resources.json"
    os.environ["SCT_START_TIME"] = str(time.time())
    # init_kwargs = get_tracer().init_kwargs
    init_kwargs = 1

    print_utils.echo(f"Running with {num_workers} processes!")
    start = time.time()
    multiprocessing.set_start_method("spawn")
    lock = multiprocessing.Lock()

    with open(resources_file_path, "w") as f:
        f.write("{}")

    task_queue = multiprocessing.Queue()
    results_queue = multiprocessing.Queue()
    resources_in_use = dict()

    processes = [
        multiprocessing.Process(
            target=worker_task,
            args=(
                lock,
                task_queue,
                results_queue,
                tasks_to_run,
                manifest_files_path,
                manifest_task_reference_file_path,
                puppet_account_id,
                resources_file_path
            ),
        )
        for i in range(num_workers)
    ]
    processes.append(
        multiprocessing.Process(
            target=scheduler,
            args=(
                num_workers,
                task_queue,
                results_queue,
                tasks_to_run,
                resources_in_use,
                manifest_files_path,
                manifest_task_reference_file_path,
                puppet_account_id,
            ),
        )
    )
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    print_utils.echo(f"Time taken = {time.time() - start:.10f}")
