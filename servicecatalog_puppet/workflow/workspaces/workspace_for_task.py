import luigi

from servicecatalog_puppet.workflow.workspaces import provision_workspace_task
from servicecatalog_puppet.workflow.workspaces import workspace_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class WorkspaceForTask(
    workspace_base_task.WorkspaceBaseTask, manifest_mixin.ManifestMixen
):
    workspace_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "workspace_name": self.workspace_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        #TODO need to add in dry run and deletion
        return provision_workspace_task.ProvisionWorkspaceTask

    def run(self):
        self.write_output(self.params_for_results_display())
