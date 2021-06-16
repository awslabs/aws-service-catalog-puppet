import json
import logging
import math
import os
import traceback
from pathlib import Path

import luigi
import psutil
from betterboto import client as betterboto_client
from luigi import format
from luigi.contrib import s3
from deepmerge import always_merger

from servicecatalog_puppet import constants, config

logger = logging.getLogger("tasks")
logger.setLevel(logging.INFO)


def unwrap(what):
    if hasattr(what, "get_wrapped"):
        thing = what.get_wrapped()
    else:
        thing = what
    if isinstance(what, dict):
        for k, v in thing.items():
            thing[k] = unwrap(v)
    return thing


class PuppetTask(luigi.Task):
    @property
    def execution_mode(self):
        return os.environ.get("SCT_EXECUTION_MODE", constants.EXECUTION_MODE_HUB)

    @property
    def single_account(self):
        return os.environ.get("SCT_SINGLE_ACCOUNT", "None")

    @property
    def should_use_product_plans(self):
        if self.execution_mode == constants.EXECUTION_MODE_HUB:
            return os.environ.get("SCT_SHOULD_USE_PRODUCT_PLANS", "True") == "True"
        else:
            return False

    @property
    def cache_invalidator(self):
        return os.environ.get("SCT_CACHE_INVALIDATOR", "NOW")

    @property
    def is_dry_run(self):
        return os.environ.get("SCT_IS_DRY_RUN", "False") == "True"

    @property
    def should_use_sns(self):
        return os.environ.get("SCT_SHOULD_USE_SNS", "False") == "True"

    def spoke_client(self, service):
        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{config.get_puppet_role_name()}",
        )

    def spoke_regional_client(self, service):
        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-{config.get_puppet_role_name()}",
            region_name=self.region,
        )

    def hub_client(self, service):
        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.puppet_account_id),
            f"{self.puppet_account_id}-{config.get_puppet_role_name()}",
        )

    def hub_regional_client(self, service, region_name=None):
        region = region_name or self.region
        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.puppet_account_id),
            f"{self.puppet_account_id}-{region}-{config.get_puppet_role_name()}",
            region_name=region,
        )

    def read_from_input(self, input_name):
        with self.input().get(input_name).open("r") as f:
            return f.read()

    def load_from_input(self, input_name):
        return json.loads(self.read_from_input(input_name))

    def info(self, message):
        logger.info(f"{self.uid}: {message}")

    def error(self, message):
        logger.error(f"{self.uid}: {message}")

    def warning(self, message):
        logger.warning(f"{self.uid}: {message}")

    def api_calls_used(self):
        return []

    @property
    def resources(self):
        result = {}
        for a in self.api_calls_used():
            result[a] = 1
        return result

    @property
    def output_location(self):
        puppet_account_id = config.get_puppet_account_id()
        path = f"output/{self.uid}.{self.output_suffix}"
        should_use_s3_target_if_caching_is_on = (
            "cache_invalidator" not in self.params_for_results_display().keys()
        )
        if should_use_s3_target_if_caching_is_on and config.is_caching_enabled(
            puppet_account_id
        ):
            return f"s3://sc-puppet-caching-bucket-{config.get_puppet_account_id()}-{config.get_home_region(puppet_account_id)}/{path}"
        else:
            return path

    def output(self):
        should_use_s3_target_if_caching_is_on = (
            "cache_invalidator" not in self.params_for_results_display().keys()
        )
        if should_use_s3_target_if_caching_is_on and config.is_caching_enabled(
            config.get_puppet_account_id()
        ):
            return s3.S3Target(self.output_location, format=format.UTF8)
        else:
            return luigi.LocalTarget(self.output_location)

    @property
    def output_suffix(self):
        return "json"

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.node_id}"

    def params_for_results_display(self):
        return {}

    def write_output(self, content, skip_json_dump=False):
        with self.output().open("w") as f:
            if skip_json_dump:
                f.write(content)
            else:
                f.write(json.dumps(content, indent=4, default=str,))

    @property
    def node_id(self):
        values = [self.__class__.__name__.replace("Task", "")] + [
            str(v) for v in self.params_for_results_display().values()
        ]
        return "/".join(values)

    def graph_node(self):
        task_friendly_name = self.__class__.__name__.replace("Task", "")
        task_description = ""
        for param, value in self.params_for_results_display().items():
            task_description += f"<br/>{param}: {value}"
        label = f"<b>{task_friendly_name}</b>{task_description}"
        return f'"{self.node_id}" [fillcolor=lawngreen style=filled label= < {label} >]'


class GetSSMParamTask(PuppetTask):
    parameter_name = luigi.Parameter()
    name = luigi.Parameter()
    region = luigi.Parameter(default=None)

    def params_for_results_display(self):
        return {
            "parameter_name": self.parameter_name,
            "name": self.name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

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
                        "Version": p.get("Parameter").get("Version"),
                    }
                )
            except ssm.exceptions.ParameterNotFound as e:
                raise e


class PuppetTaskWithParameters(PuppetTask):
    def get_all_of_the_params(self):
        all_params = dict()
        always_merger.merge(all_params, unwrap(self.manifest_parameters))
        always_merger.merge(all_params, unwrap(self.launch_parameters))
        always_merger.merge(all_params, unwrap(self.account_parameters))
        return all_params

    def get_ssm_parameters(self):
        ssm_params = dict()

        all_params = self.get_all_of_the_params()

        for param_name, param_details in all_params.items():
            if param_details.get("ssm"):
                if param_details.get("default"):
                    del param_details["default"]
                ssm_parameter_name = param_details.get("ssm").get("name")
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::Region}", self.region
                )
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::AccountId}", self.account_id
                )
                ssm_params[param_name] = GetSSMParamTask(
                    parameter_name=param_name,
                    name=ssm_parameter_name,
                    region=param_details.get("ssm").get(
                        "region", config.get_home_region(self.puppet_account_id)
                    ),
                )

        return ssm_params

    def get_parameter_values(self):
        all_params = {}
        self.info(f"collecting all_params")
        p = self.get_all_of_the_params()
        for param_name, param_details in p.items():
            if param_details.get("ssm"):
                with self.input().get("ssm_params").get(param_name).open() as f:
                    all_params[param_name] = json.loads(f.read()).get("Value")
            if param_details.get("default"):
                all_params[param_name] = param_details.get("default")
            if param_details.get("mapping"):
                all_params[param_name] = self.manifest.get_mapping(
                    param_details.get("mapping"), self.account_id, self.region
                )

        self.info(f"finished collecting all_params: {all_params}")
        return all_params


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


@luigi.Task.event_handler(luigi.Event.START)
def on_task_success(task):
    task_name = task.__class__.__name__
    to_string = f"{task_name}: "
    for name, value in task.param_kwargs.items():
        to_string += f"{name}={value}, "
    logger.info(f"{to_string} started")
    record_event("start", task)


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

    task_params = dict(**task.param_kwargs)
    task_params.update(task.params_for_results_display())

    with betterboto_client.CrossAccountClientContextManager(
        "cloudwatch",
        config.get_puppet_role_arn(config.get_puppet_account_id()),
        "cloudwatch-puppethub",
    ) as cloudwatch:

        dimensions = [dict(Name="task_type", Value=task.__class__.__name__,)]
        for note_worthy in [
            "launch_name",
            "region",
            "account_id",
            "puppet_account_id",
            "sharing_mode",
            "portfolio",
            "product",
            "version",
            "execution",
        ]:
            if task_params.get(note_worthy):
                dimensions.append(
                    dict(Name=str(note_worthy), Value=str(task_params.get(note_worthy)))
                )

        cloudwatch.put_metric_data(
            Namespace=f"ServiceCatalogTools/Puppet/v1/ProcessingTime/{task.__class__.__name__}",
            MetricData=[
                dict(
                    MetricName=task.__class__.__name__,
                    Dimensions=dimensions,
                    Value=duration,
                    Unit="Seconds",
                ),
            ],
        )
        cloudwatch.put_metric_data(
            Namespace=f"ServiceCatalogTools/Puppet/v1/ProcessingTime/Tasks",
            MetricData=[
                dict(
                    MetricName="Tasks",
                    Dimensions=[dict(Name="TaskType", Value=task.__class__.__name__)],
                    Value=duration,
                    Unit="Seconds",
                ),
            ],
        )


@luigi.Task.event_handler(luigi.Event.BROKEN_TASK)
def on_task_broken_task(task, exception):
    print_stats()
    record_event("broken_task", task, {"exception": exception})
