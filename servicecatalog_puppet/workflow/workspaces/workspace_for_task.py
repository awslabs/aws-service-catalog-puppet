#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.workspaces import provision_dry_run_workspace_task
from servicecatalog_puppet.workflow.workspaces import provision_workspace_task
from servicecatalog_puppet.workflow.workspaces import terminate_dry_run_workspace_task
from servicecatalog_puppet.workflow.workspaces import terminate_workspace_task
from servicecatalog_puppet.workflow.workspaces import workspace_base_task


class WorkspaceForTask(
    workspace_base_task.WorkspaceBaseTask, manifest_mixin.ManifestMixen
):
    workspace_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "workspace_name": self.workspace_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        if self.is_dry_run:
            if self.status == constants.PROVISIONED:
                return provision_dry_run_workspace_task.ProvisionDryRunWorkspaceTask
            elif self.status == constants.TERMINATED:
                return terminate_dry_run_workspace_task.TerminateDryRunWorkspaceTask
            else:
                raise Exception(f"Unknown status: {self.status}")

        else:
            if self.status == constants.PROVISIONED:
                return provision_workspace_task.ProvisionWorkspaceTask
            elif self.status == constants.TERMINATED:
                return terminate_workspace_task.TerminateWorkspaceTask
            else:
                raise Exception(f"Unknown status: {self.status}")

    def run(self):
        self.write_output(self.params_for_results_display())
