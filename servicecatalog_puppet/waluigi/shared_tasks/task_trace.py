#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import queue
import time

from betterboto import client as betterboto_client

from servicecatalog_puppet import (
    config,
    constants,
    environmental_variables,
    serialisation_utils,
)
from servicecatalog_puppet.commands import graph
from servicecatalog_puppet.serialisation_utils import unwrap
from servicecatalog_puppet.waluigi.dag_utils import logger


def on_task_trace(task_trace_queue, complete_event, puppet_account_id, execution_mode):
    bucket = f"sc-puppet-log-store-{puppet_account_id}"
    key_prefix = f"{os.getenv('CODEBUILD_BUILD_ID', f'local/{os.getenv(environmental_variables.DRIFT_TOKEN)}')}/traces"
    if execution_mode != constants.EXECUTION_MODE_SPOKE:
        with betterboto_client.CrossAccountClientContextManager(
            "s3", config.get_reporting_role_arn(config.get_executor_account_id()), "s3",
        ) as s3:
            while not complete_event.is_set():
                time.sleep(0.1)
                try:
                    (
                        t,
                        task_type,
                        task_params,
                        is_start,
                        thread_name,
                    ) = task_trace_queue.get(timeout=5)
                except queue.Empty:
                    continue
                else:
                    tz = (t - float(os.getenv("SCT_START_TIME", 0))) * 1000000
                    task_reference = task_params.get("task_reference")
                    s3.put_object(
                        Bucket=bucket,
                        Key=f"{key_prefix}/{tz}-{graph.escape(task_reference)}-{'start' if is_start else 'end'}.json",
                        Body=serialisation_utils.json_dumps(
                            {
                                "name": task_reference,
                                "cat": task_type,
                                "ph": "B" if is_start else "E",
                                "pid": 1,
                                "tid": thread_name,
                                "ts": tz,
                                "args": unwrap(task_params),
                            }
                        ),
                    )

        logger.info("shutting down")
