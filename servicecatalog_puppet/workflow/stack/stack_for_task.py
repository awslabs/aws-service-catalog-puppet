#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.stack import provision_stack_dry_run_task
from servicecatalog_puppet.workflow.stack import provision_stack_task
from servicecatalog_puppet.workflow.stack import provisioning_task
from servicecatalog_puppet.workflow.stack import terminate_stack_dry_run_task
from servicecatalog_puppet.workflow.stack import terminate_stack_task


class StackForTask(provisioning_task.ProvisioningTask):
    stack_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "stack_name": self.stack_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        if self.is_dry_run:
            if self.status == constants.PROVISIONED:
                return provision_stack_dry_run_task.ProvisionStackDryRunTask
            elif self.status == constants.TERMINATED:
                return terminate_stack_dry_run_task.TerminateStackDryRunTask
            else:
                raise Exception(f"Unknown status: {self.status}")
        else:
            if self.status == constants.PROVISIONED:
                return provision_stack_task.ProvisionStackTask
            elif self.status == constants.TERMINATED:
                return terminate_stack_task.TerminateStackTask
            else:
                raise Exception(f"Unknown status: {self.status}")

    def run(self):
        self.write_output(self.params_for_results_display())
