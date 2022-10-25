from servicecatalog_puppet.waluigi.threads import (
    topological_generations as threads_topological_generations,
)
from servicecatalog_puppet.waluigi.processes import (
    topological_generations as processes_topological_generations,
)


def get_scheduler(threads_or_processes: str, algorithm: str):
    name = f"{threads_or_processes}.{algorithm}"
    print(f"Using scheduler: {name}")
    if name == "threads.topological_generations":
        return threads_topological_generations
    if name == "processes.topological_generations":
        return processes_topological_generations

    raise Exception(f"Unsupported scheduler: {name}")
