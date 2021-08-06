from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.workspaces import workspace_base_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_account_and_region_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_account_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_region_task
from servicecatalog_puppet.workflow.workspaces import workspace_task
from servicecatalog_puppet.workflow.manifest import section_task
from servicecatalog_puppet.workflow.generate import generate_policies_task


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
        has_items = False

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
            has_items = True

        if has_items:
            for (
                    region_name,
                    sharing_policies,
            ) in self.manifest.get_sharing_policies_by_region().items():
                requirements.append(
                    generate_policies_task.GeneratePolicies(
                        puppet_account_id=self.puppet_account_id,
                        manifest_file_path=self.manifest_file_path,
                        region=region_name,
                        sharing_policies=sharing_policies,
                    )
                )

        return requirements

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
