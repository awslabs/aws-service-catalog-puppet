import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.general import get_ssm_param_task


class CodeBuildRunBaseTask(get_ssm_param_task.PuppetTaskWithParameters):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.CODE_BUILD_RUNS

    @property
    def item_name(self):
        return self.code_build_run_name
