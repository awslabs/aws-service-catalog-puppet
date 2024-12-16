#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from copy import deepcopy

import jmespath
import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class GetS3ObjectTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    key = luigi.Parameter()
    region = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "key": self.key,
        }

    def run(self):
        with self.spoke_regional_client("s3") as s3:
            object = (
                s3.get_object(
                    Bucket=f"sc-puppet-parameters-{self.account_id}", Key=self.key
                )
                .get("Body")
                .read()
            )
            self.write_output(object, skip_json_encode=True)
