#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path

import psutil
from betterboto import client as betterboto_client

from servicecatalog_puppet import constants, config

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def record_event(event_type, task, extra_event_data=None):
    task_type = task.__class__.__name__
    task_params = task.param_kwargs

    event = {
        "event_type": event_type,
        "task_type": task_type,
        "task_params": task_params,
        "params_for_results": task.params_for_results_display(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pid": os.getpid(),
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


def print_stats():
    pid = os.getpid()
    p = psutil.Process(pid)
    m_percent = p.memory_percent()
    memory_info = p.memory_info().rss / 1024 ** 2
    cpu_percent = p.cpu_percent(interval=1)
    logger.info(
        f"stats: process {pid} is using {memory_info}MB ({m_percent}%) of memory and {cpu_percent}% of CPU"
    )


class WaluigiTaskMixin:
    def on_task_failure(self, exception):
        exception_details = {
            "exception_type": type(exception),
            "exception_stack_trace": traceback.format_exception(
                etype=type(exception), value=exception, tb=exception.__traceback__,
            ),
        }
        record_event("failure", self, exception_details)

    def on_task_start(self):
        task_name = self.__class__.__name__
        to_string = f"{task_name}: "
        for name, value in self.param_kwargs.items():
            to_string += f"{name}={value}, "
        logger.info(f"{to_string} started")
        record_event("start", self)

    def on_task_success(self):
        print_stats()
        record_event("success", self)

    def on_task_timeout(self):
        print_stats()
        record_event("timeout", self)

    def on_task_process_failure(self, error_msg):
        print_stats()
        exception_details = {
            "exception_type": "PROCESS_FAILURE",
            "exception_stack_trace": error_msg,
        }
        record_event("process_failure", self, exception_details)

    def on_task_processing_time(self, duration):
        print_stats()
        record_event("processing_time", self, {"duration": duration})

        task_params = dict(**self.param_kwargs)
        task_params.update(self.params_for_results_display())

        with betterboto_client.CrossAccountClientContextManager(
            "cloudwatch",
            config.get_puppet_role_arn(config.get_executor_account_id()),
            "cloudwatch-puppethub",
        ) as cloudwatch:

            dimensions = [
                dict(Name="task_type", Value=self.__class__.__name__,),
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
                        dict(
                            Name=str(note_worthy),
                            Value=str(task_params.get(note_worthy)),
                        )
                    )

            cloudwatch.put_metric_data(
                Namespace=f"ServiceCatalogTools/Puppet/v2/ProcessingTime/Tasks",
                MetricData=[
                    dict(
                        MetricName="Tasks",
                        Dimensions=[
                            dict(Name="TaskType", Value=self.__class__.__name__)
                        ]
                        + dimensions,
                        Value=duration,
                        Unit="Seconds",
                    ),
                ],
            )

    def on_task_broken_task(self, exception):
        print_stats()
        record_event("broken_task", self, {"exception": exception})
