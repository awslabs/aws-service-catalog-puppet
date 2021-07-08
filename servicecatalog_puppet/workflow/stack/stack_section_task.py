from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.stack import stack_for_account_and_region_task
from servicecatalog_puppet.workflow.stack import stack_for_account_task
from servicecatalog_puppet.workflow.stack import stack_for_region_task
from servicecatalog_puppet.workflow.stack import stack_for_spoke_execution_task
from servicecatalog_puppet.workflow.stack import stack_task
from servicecatalog_puppet.workflow.manifest import section_task


class StackSectionTask(section_task.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        self.info(f"Stacks and execution mode is: {self.execution_mode}")
        requirements = list()

        for name, details in self.manifest.get(constants.STACKS, {}).items():
            execution = details.get("execution")

            if self.is_running_in_spoke():
                if execution == constants.EXECUTION_MODE_SPOKE:
                    requirements += self.handle_requirements_for(
                        name,
                        constants.STACK,
                        constants.STACKS,
                        stack_for_region_task.StackForRegionTask,
                        stack_for_account_task.StackForAccountTask,
                        stack_for_account_and_region_task.StackForAccountAndRegionTask,
                        stack_task.StackTask,
                        dict(
                            stack_name=name,
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
                        constants.STACK,
                        constants.STACKS,
                        stack_for_region_task.StackForRegionTask,
                        stack_for_account_task.StackForAccountTask,
                        stack_for_account_and_region_task.StackForAccountAndRegionTask,
                        stack_task.StackTask,
                        dict(
                            stack_name=name,
                            puppet_account_id=self.puppet_account_id,
                            manifest_file_path=self.manifest_file_path,
                        ),
                    )
                else:
                    requirements.append(
                        stack_for_spoke_execution_task.StackForSpokeExecutionTask(
                            stack_name=name,
                            puppet_account_id=self.puppet_account_id,
                            manifest_file_path=self.manifest_file_path,
                        )
                    )

        return requirements

    def run(self):
        self.write_output(self.manifest.get(constants.STACKS, {}))
