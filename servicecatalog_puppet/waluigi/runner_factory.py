from servicecatalog_puppet.waluigi.threads import (
    runner as threads_runner,

)
from servicecatalog_puppet.waluigi.processes import (
    runner as processes_runner,
)


def get_runner(threads_or_processes: str):
    threads_or_processes = "processes"
    if threads_or_processes == "threads":
        return threads_runner
    elif threads_or_processes == "processes":
        return processes_runner

    raise ValueError(f"threads_or_processes invalid: {threads_or_processes}")
