#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.workspaces import create_template_for_workspace_task


class PrepareAccountForWorkspaceTask(tasks.PuppetTask):
    account_id = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
        }

    def requires(self):
        return create_template_for_workspace_task.CreateTemplateForWorkspaceTask(
            self.puppet_account_id
        )

    def api_calls_used(self):
        return {
            f"cloudformation.create_or_update_{self.account_id}": 1,
        }

    def run(self):
        template = self.input().open("r").read()
        with self.spoke_client("cloudformation") as cloudformation:
            cloudformation.create_or_update(
                StackName=constants.TERRAFORM_SPOKE_PREP_STACK_NAME,
                TemplateBody=template,
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )

        self.write_output(self.params_for_results_display())
