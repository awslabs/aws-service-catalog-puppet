#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.launch import run_deploy_in_spoke_task


class GenericScheduleRunDeployInSpokeTask(
    tasks.PuppetTask, manifest_mixin.ManifestMixen
):
    section_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "section_name": self.section_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        tasks_to_run = list()
        for name, details in self.manifest.get(self.section_name, {}).items():
            should_item_not_be_ignored = (
                details.get(constants.MANIFEST_STATUS_FIELD_NAME)
                != constants.MANIFEST_STATUS_FIELD_VALUE_IGNORED
            )
            if should_item_not_be_ignored:
                should_be_executed_in_a_spoke = (
                    details.get("execution", constants.EXECUTION_MODE_DEFAULT)
                    == constants.EXECUTION_MODE_SPOKE
                )
                can_be_executed_in_a_spoke = (
                    details.get("execution", constants.EXECUTION_MODE_DEFAULT)
                    == constants.EXECUTION_MODE_HUB_AND_SPOKE_SPLIT
                )
                if should_be_executed_in_a_spoke or can_be_executed_in_a_spoke:
                    for (
                        account_id
                    ) in self.manifest.get_account_ids_used_for_section_item(
                        self.puppet_account_id, self.section_name, name
                    ):
                        tasks_to_run.append(
                            run_deploy_in_spoke_task.RunDeployInSpokeTask(
                                manifest_file_path=self.manifest_file_path,
                                puppet_account_id=self.puppet_account_id,
                                account_id=account_id,
                            )
                        )
        return tasks_to_run

    def run(self):
        self.write_output(self.params_for_results_display())
