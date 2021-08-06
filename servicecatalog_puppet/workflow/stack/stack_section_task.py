from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.stack import stack_for_account_and_region_task
from servicecatalog_puppet.workflow.stack import stack_for_account_task
from servicecatalog_puppet.workflow.stack import stack_for_region_task
from servicecatalog_puppet.workflow.stack import stack_task
from servicecatalog_puppet.workflow.manifest import section_task
from servicecatalog_puppet.workflow.launch import run_deploy_in_spoke_task


class StackSectionTask(section_task.SectionTask):

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()

        for name, details in self.manifest.get(constants.STACKS, {}).items():
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

        return requirements

    def run(self):
        if not self.is_running_in_spoke():
            tasks_to_run = list()
            for name, details in self.manifest.get(constants.STACKS, {}).items():
                for account_id in self.manifest.get_account_ids_used_for_section_item(
                        self.puppet_account_id, constants.STACKS, name
                ):
                    tasks_to_run.append(
                        run_deploy_in_spoke_task.RunDeployInSpokeTask(
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            account_id=account_id,
                        )
                    )
            yield tasks_to_run
        self.write_output(self.manifest.get(constants.STACKS, {}))
