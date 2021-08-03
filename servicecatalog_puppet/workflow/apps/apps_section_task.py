from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.apps import app_base_task
from servicecatalog_puppet.workflow.apps import (
    app_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.apps import app_for_account_task
from servicecatalog_puppet.workflow.apps import app_for_region_task
from servicecatalog_puppet.workflow.apps import app_task
from servicecatalog_puppet.workflow.manifest import section_task


class AppsSectionTask(
    app_base_task.AppBaseTask, section_task.SectionTask
):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()

        for name, details in self.manifest.get(constants.APPS, {}).items():
            requirements += self.handle_requirements_for(
                name,
                constants.APP,
                constants.APPS,
                app_for_region_task.AppForRegionTask,
                app_for_account_task.AppForAccountTask,
                app_for_account_and_region_task.AppForAccountAndRegionTask,
                app_task.AppTask,
                dict(
                    app_name=name,
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                ),
            )

        return requirements

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
