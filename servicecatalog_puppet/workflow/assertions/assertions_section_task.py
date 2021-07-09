from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.assertions import assertion_base_task
from servicecatalog_puppet.workflow.assertions import (
    assertion_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.assertions import assertion_for_account_task
from servicecatalog_puppet.workflow.assertions import assertion_for_region_task
from servicecatalog_puppet.workflow.assertions import assertion_task
from servicecatalog_puppet.workflow.manifest import section_task


class AssertionsSectionTask(
    assertion_base_task.AssertionBaseTask, section_task.SectionTask
):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()

        for name, details in self.manifest.get(constants.ASSERTIONS, {}).items():
            requirements += self.handle_requirements_for(
                name,
                constants.ASSERTION,
                constants.ASSERTIONS,
                assertion_for_region_task.AssertionForRegionTask,
                assertion_for_account_task.AssertionForAccountTask,
                assertion_for_account_and_region_task.AssertionForAccountAndRegionTask,
                assertion_task.AssertionTask,
                dict(
                    assertion_name=name,
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                ),
            )

        return requirements

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
