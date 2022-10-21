#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
import os
import traceback
from datetime import datetime
from pathlib import Path

import luigi
from betterboto import client as betterboto_client
from luigi import format
from luigi.contrib import s3

from servicecatalog_puppet import (
    constants,
    config,
    environmental_variables,
    serialisation_utils,
)

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def unwrap(what):
    if hasattr(what, "get_wrapped"):
        return unwrap(what.get_wrapped())

    if isinstance(what, dict):
        thing = dict()
        for k, v in what.items():
            thing[k] = unwrap(v)
        return thing

    if isinstance(what, tuple):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    if isinstance(what, list):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    return what


class PuppetTask(luigi.Task):
    @property
    def initialiser_stack_tags(self):
        initialiser_stack_tags_value = os.environ.get(
            environmental_variables.INITIALISER_STACK_TAGS, None
        )
        if initialiser_stack_tags_value is None:
            raise Exception(
                f"You must export {environmental_variables.INITIALISER_STACK_TAGS}"
            )
        return serialisation_utils.json_loads(initialiser_stack_tags_value)

    @property
    def executor_account_id(self):
        return os.environ.get(environmental_variables.EXECUTOR_ACCOUNT_ID)

    @property
    def execution_mode(self):
        return os.environ.get(
            environmental_variables.EXECUTION_MODE, constants.EXECUTION_MODE_HUB
        )

    @property
    def spoke_execution_mode_deploy_env(self):
        return os.environ.get(
            environmental_variables.SPOKE_EXECUTION_MODE_DEPLOY_ENV,
            constants.SPOKE_EXECUTION_MODE_DEPLOY_ENV_DEFAULT,
        )

    @property
    def should_delete_rollback_complete_stacks(self):
        return (
            str(
                os.environ.get(
                    environmental_variables.SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS,
                    constants.CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS_DEFAULT,
                )
            ).upper()
            == "TRUE"
        )

    def is_running_in_spoke(self):
        return self.execution_mode == constants.EXECUTION_MODE_SPOKE

    @property
    def single_account(self):
        return os.environ.get("SCT_SINGLE_ACCOUNT", "None")

    @property
    def should_use_product_plans(self):
        if self.execution_mode == constants.EXECUTION_MODE_HUB:
            return (
                os.environ.get(environmental_variables.SHOULD_USE_PRODUCT_PLANS, "True")
                == "True"
            )
        else:
            return False

    @property
    def cache_invalidator(self):
        return os.environ.get(environmental_variables.CACHE_INVALIDATOR, "NOW")

    @property
    def is_dry_run(self):
        return os.environ.get("SCT_IS_DRY_RUN", "False") == "True"

    @property
    def should_use_sns(self):
        return os.environ.get(environmental_variables.SHOULD_USE_SNS, "False") == "True"

    def get_account_used(self):
        return self.account_id if self.is_running_in_spoke() else self.puppet_account_id

    def spoke_client(self, service):
        kwargs = dict()
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")
        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{config.get_puppet_role_name()}",
            **kwargs,
        )

    def cross_account_client(self, account_id, service, region_name=None):
        region = region_name or self.region
        kwargs = dict(region_name=region)
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")

        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(account_id),
            f"{account_id}-{region}-{config.get_puppet_role_name()}",
            **kwargs,
        )

    def spoke_regional_client(self, service, region_name=None):
        region = region_name or self.region
        kwargs = dict(region_name=region)
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")

        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{region}-{config.get_puppet_role_name()}",
            **kwargs,
        )

    def hub_client(self, service):
        kwargs = dict()
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")
        if self.is_running_in_spoke():
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.executor_account_id),
                f"{self.executor_account_id}-{config.get_puppet_role_name()}",
                **kwargs,
            )
        else:
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.puppet_account_id),
                f"{self.puppet_account_id}-{config.get_puppet_role_name()}",
                **kwargs,
            )

    def hub_regional_client(self, service, region_name=None):
        region = region_name or self.region
        kwargs = dict(region_name=region)
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")

        if self.is_running_in_spoke():
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.executor_account_id),
                f"{self.executor_account_id}-{config.get_puppet_role_name()}",
                **kwargs,
            )
        else:
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.puppet_account_id),
                f"{self.puppet_account_id}-{region}-{config.get_puppet_role_name()}",
                **kwargs,
            )

    def organizations_policy_client(self):
        kwargs = dict()
        if os.environ.get(f"CUSTOM_ENDPOINT_organizations"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_organizations")
        if self.is_running_in_spoke():
            raise Exception("Cannot use organizations client in spoke execution")
        else:
            return betterboto_client.CrossAccountClientContextManager(
                "organizations",
                config.get_org_scp_role_arn(self.puppet_account_id),
                "org_scp_role_arn",
            )

    def read_from_input(self, input_name):
        with self.input().get(input_name).open("rb") as f:
            return f.read()

    def load_from_input(self, input_name):
        return serialisation_utils.json_loads(self.read_from_input(input_name))

    def info(self, message):
        logger.info(f"{self.uid}: {message}")

    def debug(self, message):
        logger.debug(f"{self.uid}: {message}")

    def error(self, message):
        logger.error(f"{self.uid}: {message}")

    def warning(self, message):
        logger.warning(f"{self.uid}: {message}")

    def get_output_location_path(self):
        return f"output/{self.uid}.{self.output_suffix}"

    @property
    def cached_output_location(self):
        puppet_account_id = config.get_puppet_account_id()
        path = self.get_output_location_path()
        return f"s3://sc-puppet-caching-bucket-{config.get_puppet_account_id()}-{config.get_home_region(puppet_account_id)}/{path}"

    @property
    def output_location(self):
        if self.should_use_caching:
            return self.cached_output_location
        else:
            return self.get_output_location_path()

    @property
    def should_use_caching(self):
        return (
            self.should_use_s3_target_if_caching_is_on and config.is_caching_enabled()
        )

    @property
    def should_use_s3_target_if_caching_is_on(self):
        return "cache_invalidator" not in self.params_for_results_display().keys()

    def output(self):
        if self.should_use_caching:
            return s3.S3Target(self.output_location, format=format.UTF8)
        else:
            return luigi.LocalTarget(self.output_location, format=luigi.format.Nop)

    @property
    def output_suffix(self):
        return "json"

    @property
    def uid(self):
        return f"{self.__class__.__name__}/{self.node_id}"

    def params_for_results_display(self):
        return {}

    def write_empty_output(self):
        if self.should_use_caching:
            with self.output().open("w") as f:
                f.write("{}")
        else:
            with self.output().open("wb") as f:
                f.write(b"{}")

    def write_output(self, content):
        if self.should_use_caching:
            with self.output().open("w") as f:
                f.write(serialisation_utils.json_dumps(content).decode("utf-8"))
        else:
            with self.output().open("wb") as f:
                f.write(serialisation_utils.json_dumps(content))

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


def record_event(event_type, task, extra_event_data=None):
    task_type = task.__class__.__name__
    task_params = task.param_kwargs
    pid = os.getpid()

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event = {
        "event_type": event_type,
        "task_type": task_type,
        "task_params": task_params,
        "params_for_results": task.params_for_results_display(),
        "datetime": current_datetime,
        "pid": pid,
    }
    if extra_event_data is not None:
        event.update(extra_event_data)

    with open(
        Path(constants.RESULTS_DIRECTORY)
        / event_type
        / f"{task_type}-{task.task_id}.json",
        "wb",
    ) as f:
        f.write(serialisation_utils.json_dumps(event, default=str, indent=4,))

    if event_type in ["start", "success", "failure"]:
        task_reference = task.task_reference
        t = {
            "name": task_reference,
            "cat": event_type,
            "ph": "B" if event_type == "start" else "E",
            "pid": pid,
            "tid": 1,
            "ts": current_datetime,
        }
        with open(
            Path(constants.RESULTS_DIRECTORY)
            / "traces"
            / f"{current_datetime}-{task_reference}-{event_type}.json",
            "wb",
        ) as f:
            f.write(serialisation_utils.json_dumps(t, default=str, indent=4,))


def print_stats():
    pass
    # pid = os.getpid()
    # p = psutil.Process(pid)
    # m_percent = p.memory_percent()
    # memory_info = p.memory_info().rss / 1024 ** 2
    # cpu_percent = p.cpu_percent(interval=1)
    # logger.info(
    #     f"stats: process {pid} is using {memory_info}MB ({m_percent}%) of memory and {cpu_percent}% of CPU"
    # )


@luigi.Task.event_handler(luigi.Event.FAILURE)
def on_task_failure(task, exception):
    exception_details = {
        "exception_type": type(exception),
        "exception_stack_trace": traceback.format_exception(
            etype=type(exception), value=exception, tb=exception.__traceback__,
        ),
    }
    record_event("failure", task, exception_details)


@luigi.Task.event_handler(luigi.Event.START)
def on_task_start(task):
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
        config.get_puppet_role_arn(config.get_executor_account_id()),
        "cloudwatch-puppethub",
    ) as cloudwatch:

        dimensions = [
            dict(Name="task_type", Value=task.__class__.__name__,),
            dict(
                Name="codebuild_build_id",
                Value=os.getenv("CODEBUILD_BUILD_ID", "LOCAL_BUILD"),
            ),
        ]
        for note_worthy in [
            "launch_name",
            "region",
            "account_id",
            "puppet_account_id",
            "portfolio",
            "product",
            "version",
        ]:
            if task_params.get(note_worthy):
                dimensions.append(
                    dict(Name=str(note_worthy), Value=str(task_params.get(note_worthy)))
                )

        cloudwatch.put_metric_data(
            Namespace=f"ServiceCatalogTools/Puppet/v2/ProcessingTime/Tasks",
            MetricData=[
                dict(
                    MetricName="Tasks",
                    Dimensions=[dict(Name="TaskType", Value=task.__class__.__name__)]
                    + dimensions,
                    Value=duration,
                    Unit="Seconds",
                ),
            ],
        )


@luigi.Task.event_handler(luigi.Event.BROKEN_TASK)
def on_task_broken_task(task, exception):
    print_stats()
    record_event("broken_task", task, {"exception": exception})
