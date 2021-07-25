import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.general import get_ssm_param_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class ProvisioningTask(
    get_ssm_param_task.PuppetTaskWithParameters, manifest_mixin.ManifestMixen
):
    manifest_file_path = luigi.Parameter()

    @property
    def status(self):
        return (
            self.manifest.get(constants.LAUNCHES)
            .get(self.launch_name)
            .get("status", constants.PROVISIONED)
        )

    @property
    def section_name(self):
        return constants.LAUNCHES

    @property
    def item_name(self):
        return self.launch_name
