#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import queue
import time

from betterboto import client as betterboto_client

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.waluigi.dag_utils import logger


def on_task_processing_time_task(
    task_processing_time_queue, complete_event, execution_mode
):
    if execution_mode != constants.EXECUTION_MODE_SPOKE:
        with betterboto_client.CrossAccountClientContextManager(
            "cloudwatch",
            config.get_reporting_role_arn(config.get_executor_account_id()),
            "cloudwatch-puppethub",
        ) as cloudwatch:
            while not complete_event.is_set():
                time.sleep(0.1)
                try:
                    duration, task_type, task_params = task_processing_time_queue.get(
                        timeout=5
                    )
                except queue.Empty:
                    continue
                else:
                    dimensions = [
                        dict(Name="task_type", Value=task_type,),
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
                                Dimensions=[dict(Name="TaskType", Value=task_type)]
                                + dimensions,
                                Value=duration,
                                Unit="Seconds",
                            ),
                        ],
                    )
        logger.info("shutting down")
