from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.workspaces import workspace_base_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_account_and_region_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_account_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_region_task
from servicecatalog_puppet.workflow.workspaces import workspace_task
from servicecatalog_puppet.workflow.manifest import section_task


class WorkspaceSectionTask(
    workspace_base_task.WorkspaceBaseTask, section_task.SectionTask
):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()

        for name, details in self.manifest.get(constants.WORKSPACES, {}).items():
            requirements += self.handle_requirements_for(
                name,
                constants.WORKSPACE,
                constants.WORKSPACES,
                workspace_for_region_task.WorkspaceForRegionTask,
                workspace_for_account_task.WorkspaceForAccountTask,
                workspace_for_account_and_region_task.WorkspaceForAccountAndRegionTask,
                workspace_task.WorkspaceTask,
                dict(
                    workspace_name=name,
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                ),
            )

        return requirements

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
