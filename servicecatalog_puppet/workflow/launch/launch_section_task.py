from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.launch import launch_for_account_and_region_task
from servicecatalog_puppet.workflow.launch import launch_for_account_task
from servicecatalog_puppet.workflow.launch import launch_for_region_task
from servicecatalog_puppet.workflow.launch import launch_for_spoke_execution_task
from servicecatalog_puppet.workflow.launch import launch_task
from servicecatalog_puppet.workflow.manifest import section_task


class LaunchSectionTask(section_task.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        self.info(f"Launching and execution mode is: {self.execution_mode}")
        requirements = list()

        for name, details in self.manifest.get(constants.LAUNCHES, {}).items():
            execution = details.get("execution")

            if self.is_running_in_spoke():
                if execution == constants.EXECUTION_MODE_SPOKE:
                    requirements += self.handle_requirements_for(
                        name,
                        constants.LAUNCH,
                        constants.LAUNCHES,
                        launch_for_region_task.LaunchForRegionTask,
                        launch_for_account_task.LaunchForAccountTask,
                        launch_for_account_and_region_task.LaunchForAccountAndRegionTask,
                        launch_task.LaunchTask,
                        dict(
                            launch_name=name,
                            puppet_account_id=self.puppet_account_id,
                            manifest_file_path=self.manifest_file_path,
                        ),
                    )
                else:
                    continue

            else:
                if execution != constants.EXECUTION_MODE_SPOKE:
                    requirements += self.handle_requirements_for(
                        name,
                        constants.LAUNCH,
                        constants.LAUNCHES,
                        launch_for_region_task.LaunchForRegionTask,
                        launch_for_account_task.LaunchForAccountTask,
                        launch_for_account_and_region_task.LaunchForAccountAndRegionTask,
                        launch_task.LaunchTask,
                        dict(
                            launch_name=name,
                            puppet_account_id=self.puppet_account_id,
                            manifest_file_path=self.manifest_file_path,
                        ),
                    )
                else:
                    requirements.append(
                        launch_for_spoke_execution_task.LaunchForSpokeExecutionTask(
                            launch_name=name,
                            puppet_account_id=self.puppet_account_id,
                            manifest_file_path=self.manifest_file_path,
                        )
                    )

        return requirements

    def run(self):
        self.write_output(self.manifest.get(constants.LAUNCHES, {}))
