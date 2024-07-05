#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class TerminateCloudFormationStackTask(tasks.TaskWithReference):
    stack_name = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    execution = luigi.Parameter()

    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "stack_name": self.stack_name,
            "account_id": self.account_id,
            "region": self.region,
        }

    def run(self):
        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.ensure_deleted(StackName=self.stack_name)
        self.write_empty_output()
