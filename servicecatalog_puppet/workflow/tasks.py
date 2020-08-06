import json
import traceback
from pathlib import Path

import luigi
from betterboto import client as betterboto_client

from servicecatalog_puppet import constants
import psutil
import logging
import math

logger = logging.getLogger("tasks")


class PuppetTask(luigi.Task):
    def read_from_input(self, input_name):
        with self.input().get(input_name).open("r") as f:
            return f.read()

    def load_from_input(self, input_name):
        return json.loads(self.read_from_input(input_name))

    def info(self, message):
        logger.info(f"{self.uid}: {message}")

    def error(self, message):
        logger.error(f"{self.uid}: {message}")

    def api_calls_used(self):
        return []

    @property
    def resources(self):
        result = {}
        for a in self.api_calls_used():
            result[a] = 1
        return result

    def output(self):
        return luigi.LocalTarget(f"output/{self.uid}.json")

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.node_id}"

    def params_for_results_display(self):
        return {}

    def write_output(self, content):
        with self.output().open("w") as f:
            f.write(json.dumps(content, indent=4, default=str,))

    @property
    def node_id(self):
        values = [str(v) for v in self.params_for_results_display().values()]
        return f"{self.__class__.__name__}_{'|'.join(values)}"

    def graph_node(self):
        task_friendly_name = self.__class__.__name__.replace("Task", "")
        task_description = ""
        for param, value in self.params_for_results_display().items():
            task_description += f"<br/>{param}: {value}"
        label = f"<b>{task_friendly_name}</b>{task_description}"
        return f'"{self.node_id}" [fillcolor=lawngreen style=filled label= < {label} >]'

    def get_lines(self, haystack):
        lines = []
        if isinstance(haystack, list):
            for i in haystack:
                lines += self.get_lines(i)
        elif isinstance(haystack, dict):
            for i in haystack.values():
                lines += self.get_lines(i)
        else:
            lines.append(f'"{self.node_id}" -> "{haystack.node_id}"')
        return lines

    def get_graph_lines(self):
        return self.get_lines(self.requires())


class GetSSMParamTask(PuppetTask):
    parameter_name = luigi.Parameter()
    name = luigi.Parameter()
    region = luigi.Parameter(default=None)

    def params_for_results_display(self):
        return {
            "parameter_name": self.parameter_name,
            "name": self.name,
            "region": self.region,
        }

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.__class__.__name__}/" f"{self.uid}.json"
        )

    def api_calls_used(self):
        return ["ssm.get_parameter"]

    def run(self):
        with betterboto_client.ClientContextManager(
            "ssm", region_name=self.region
        ) as ssm:
            try:
                p = ssm.get_parameter(Name=self.name,)
                self.write_output(
                    {
                        "Name": self.name,
                        "Region": self.region,
                        "Value": p.get("Parameter").get("Value"),
                    }
                )
            except ssm.exceptions.ParameterNotFound as e:
                raise e


def record_event(event_type, task, extra_event_data=None):
    task_type = task.__class__.__name__
    task_params = task.param_kwargs

    event = {
        "event_type": event_type,
        "task_type": task_type,
        "task_params": task_params,
        "params_for_results": task.params_for_results_display(),
    }
    if extra_event_data is not None:
        event.update(extra_event_data)

    with open(
        Path(constants.RESULTS_DIRECTORY)
        / event_type
        / f"{task_type}-{task.task_id}.json",
        "w",
    ) as f:
        f.write(json.dumps(event, default=str, indent=4,))


@luigi.Task.event_handler(luigi.Event.FAILURE)
def on_task_failure(task, exception):
    exception_details = {
        "exception_type": type(exception),
        "exception_stack_trace": traceback.format_exception(
            etype=type(exception), value=exception, tb=exception.__traceback__,
        ),
    }
    record_event("failure", task, exception_details)


def print_stats():
    mem = psutil.virtual_memory()
    logger.info(
        f"memory usage: total={math.ceil(mem.total / 1024 / 1024)}MB used={math.ceil(mem.used / 1024 / 1024)}MB percent={mem.percent}%"
    )


@luigi.Task.event_handler(luigi.Event.SUCCESS)
def on_task_success(task):
    print_stats()
    record_event("success", task)


@luigi.Task.event_handler(luigi.Event.TIMEOUT)
def on_task_timeout(task):
    print_stats()
    record_event("timeout", task)


@luigi.Task.event_handler(luigi.Event.PROCESS_FAILURE)
def on_task_process_failure(task, error_msg):
    print_stats()
    exception_details = {
        "exception_type": "PROCESS_FAILURE",
        "exception_stack_trace": error_msg,
    }
    record_event("process_failure", task, exception_details)


@luigi.Task.event_handler(luigi.Event.PROCESSING_TIME)
def on_task_processing_time(task, duration):
    print_stats()
    record_event("processing_time", task, {"duration": duration})


@luigi.Task.event_handler(luigi.Event.BROKEN_TASK)
def on_task_broken_task(task, exception):
    print_stats()
    record_event("broken_task", task, {"exception": exception})
