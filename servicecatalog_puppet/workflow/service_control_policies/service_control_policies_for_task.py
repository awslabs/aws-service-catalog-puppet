#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.service_control_policies import (
    service_control_policies_base_task,
)
from servicecatalog_puppet.workflow.service_control_policies import (
    execute_service_control_policies_task,
    terminate_service_control_policies_task,
)
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class ServiceControlPoliciesForTask(
    service_control_policies_base_task.ServiceControlPoliciesBaseTask,
    manifest_mixin.ManifestMixen,
):
    service_control_policy_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "service_control_policy_name": self.service_control_policy_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        if self.status == constants.PROVISIONED:
            return (
                execute_service_control_policies_task.ExecuteServiceControlPoliciesTask
            )
        elif self.status == constants.TERMINATED:
            return (
                terminate_service_control_policies_task.TerminateServiceControlPoliciesTask
            )
        else:
            raise Exception(f"Unknown status: {self.status}")

    def run(self):
        self.write_output(self.params_for_results_display())
