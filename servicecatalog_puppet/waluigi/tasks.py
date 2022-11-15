#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path

from servicecatalog_puppet import constants

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


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


class WaluigiTaskMixin:
    def execute(self):
        if self.should_use_caching:
            if self.complete():
                s3_location = self.output().path
                s3_url = s3_location.split("/")
                bucket = s3_url[2]
                key = "/".join(s3_url[3:])
                if key.endswith("latest.json"):
                    target = key
                else:
                    target = ".".join(key.split(".")[0:-1])
                target_dir = target.replace("/latest.json", "")
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                if not os.path.exists(target):
                    with self.hub_client("s3") as s3:
                        s3.download_file(Bucket=bucket, Key=key, Filename=target)
                if not os.path.exists(target):
                    raise Exception(f"{target} was not downloaded from the cache")
            else:
                self.run()
                self.execute()
        else:
            if not self.complete():
                self.run()

    def get_processing_time_details(self):
        task_details = dict(**self.param_kwargs)
        task_details.update(self.params_for_results_display())
        return self.__class__.__name__, task_details

    def on_task_failure(self, exception, duration):
        exception_details = {
            "exception_type": type(exception),
            "exception_stack_trace": traceback.format_exception(
                etype=type(exception), value=exception, tb=exception.__traceback__,
            ),
            "duration": duration,
        }
        record_event("failure", self, exception_details)

    def on_task_start(self):
        task_name = self.__class__.__name__
        logger.info(f"{task_name}:{self.task_reference} started")
        record_event("start", self)

    def on_task_success(self, duration):
        record_event("success", self, dict(duration=duration))

    def on_task_timeout(self):
        record_event("timeout", self)

    def on_task_process_failure(self, error_msg):
        exception_details = {
            "exception_type": "PROCESS_FAILURE",
            "exception_stack_trace": error_msg,
        }
        record_event("process_failure", self, exception_details)

    def on_task_broken_task(self, exception):
        record_event("broken_task", self, {"exception": exception})
