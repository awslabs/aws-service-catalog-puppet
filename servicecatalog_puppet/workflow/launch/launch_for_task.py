#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.launch import provision_product_dry_run_task
from servicecatalog_puppet.workflow.launch import provision_product_task
from servicecatalog_puppet.workflow.launch import provisioning_task
from servicecatalog_puppet.workflow.launch import terminate_product_dry_run_task
from servicecatalog_puppet.workflow.launch import terminate_product_task


class LaunchForTask(provisioning_task.ProvisioningTask):
    launch_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        if self.is_dry_run:
            if self.status == constants.PROVISIONED:
                return provision_product_dry_run_task.ProvisionProductDryRunTask
            elif self.status == constants.TERMINATED:
                return terminate_product_dry_run_task.TerminateProductDryRunTask
            else:
                raise Exception(f"Unknown status: {self.status}")
        else:
            if self.status == constants.PROVISIONED:
                return provision_product_task.ProvisionProductTask
            elif self.status == constants.TERMINATED:
                return terminate_product_task.TerminateProductTask
            else:
                raise Exception(f"Unknown status: {self.status}")

    def run(self):
        self.write_output(self.params_for_results_display())
