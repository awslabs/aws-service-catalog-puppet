import luigi

from servicecatalog_puppet.workflow.workspaces import workspace_for_task


class WorkspaceForAccountTask(workspace_for_task.WorkspaceForTask):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "workspace_name": self.workspace_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_account(
            self.puppet_account_id,
            self.section_name,
            self.workspace_name,
            self.account_id,
            single_account=self.single_account,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
