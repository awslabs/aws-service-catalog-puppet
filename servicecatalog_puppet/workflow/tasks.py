import json
import traceback
from pathlib import Path

import luigi
from betterboto import client as betterboto_client

from servicecatalog_puppet import constants


class PuppetTask(luigi.Task):

    @property
    def resources(self):
        resources_for_this_task = {}
        resource_parts = []
        if hasattr(self, 'region'):
            resource_parts.append(self.region)
        if hasattr(self, 'account_id'):
            resource_parts.append(self.account_id)

        if len(resource_parts) > 0:
            resources_for_this_task["_".join(resource_parts)] = 1

        return resources_for_this_task

    def params_for_results_display(self):
        return "Omitted"

    def write_output(self, content):
        with self.output().open('w') as f:
            f.write(
                json.dumps(
                    content,
                    indent=4,
                    default=str,
                )
            )


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

    @property
    def uid(self):
        return f"{self.region}-{self.parameter_name}-{self.name}"

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.__class__.__name__}/"
            f"{self.uid}.json"
        )

    def run(self):
        with betterboto_client.ClientContextManager('ssm', region_name=self.region) as ssm:
            try:
                p = ssm.get_parameter(
                    Name=self.name,
                )
                self.write_output({
                    'Name': self.name,
                    'Region': self.region,
                    'Value': p.get('Parameter').get('Value')
                })
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
            Path(constants.RESULTS_DIRECTORY) / event_type / f"{task_type}-{task.task_id}.json", 'w'
    ) as f:
        f.write(
            json.dumps(
                event,
                default=str,
                indent=4,
            )
        )


@luigi.Task.event_handler(luigi.Event.FAILURE)
def on_task_failure(task, exception):
    exception_details = {
        "exception_type": type(exception),
        "exception_stack_trace": traceback.format_exception(
            etype=type(exception),
            value=exception,
            tb=exception.__traceback__,
        )
    }
    record_event('failure', task, exception_details)


@luigi.Task.event_handler(luigi.Event.SUCCESS)
def on_task_success(task):
    record_event('success', task)


@luigi.Task.event_handler(luigi.Event.TIMEOUT)
def on_task_timeout(task):
    record_event('timeout', task)


@luigi.Task.event_handler(luigi.Event.PROCESS_FAILURE)
def on_task_process_failure(task, error_msg):
    exception_details = {
        "exception_type": 'PROCESS_FAILURE',
        "exception_stack_trace": error_msg,
    }
    record_event('process_failure', task, exception_details)


@luigi.Task.event_handler(luigi.Event.PROCESSING_TIME)
def on_task_processing_time(task, duration):
    record_event('processing_time', task, {"duration": duration})


@luigi.Task.event_handler(luigi.Event.BROKEN_TASK)
def on_task_broken_task(task, exception):
    record_event('broken_task', task, {"exception": exception})
