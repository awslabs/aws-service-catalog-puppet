import luigi

from servicecatalog_puppet.workflow.apps import app_task
from servicecatalog_puppet.workflow.apps import app_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class AppForTask(
    app_base_task.AppBaseTask, manifest_mixin.ManifestMixen
):
    app_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "app_name": self.app_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return app_task.AppTask

    def run(self):
        self.write_output(self.params_for_results_display())
