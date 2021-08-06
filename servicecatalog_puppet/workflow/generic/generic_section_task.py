#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.launch import run_deploy_in_spoke_task
from servicecatalog_puppet.workflow.manifest import section_task


class GenericSectionTask(section_task.SectionTask):

    section_name_singular = "not_set"
    section_name = "not_set"
    for_region_task_klass = "not_set"
    for_account_task_klass = "not_set"
    for_account_and_region_task_klass = "not_set"
    task_klass = "not_set"
    item_name = "not_set"
    supports_spoke_mode = False

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()
        common_args = dict(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
        )

        for name, details in self.manifest.get(self.section_name, {}).items():
            common_args[self.item_name] = name
            requirements += self.handle_requirements_for(
                name,
                self.section_name_singular,
                self.section_name,
                self.for_region_task_klass,
                self.for_account_task_klass,
                self.for_account_and_region_task_klass,
                self.task_klass,
                common_args,
                self.supports_spoke_mode,
            )

        return requirements

    def run(self):
        if self.supports_spoke_mode and not self.is_running_in_spoke():
            tasks_to_run = list()
            for name, details in self.manifest.get(self.section_name, {}).items():
                if (
                    details.get("execution", constants.EXECUTION_MODE_DEFAULT)
                    == constants.EXECUTION_MODE_SPOKE
                ):
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
            yield tasks_to_run
        self.write_output(self.manifest.get(self.section_name, {}))
