import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.apps import app_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class ProvisionAppTask(
    app_base_task.AppBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    app_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    expected = luigi.DictParameter()
    actual = luigi.DictParameter()

    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "app_name": self.app_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = {"section_dependencies": self.get_section_dependencies()}
        return requirements

    def run(self):
        raise Exception("We made it!")
        self.write_output(self.params_for_results_display())
