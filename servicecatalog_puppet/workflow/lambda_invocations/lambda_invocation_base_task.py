import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks


class LambdaInvocationBaseTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.LAMBDA_INVOCATIONS

    @property
    def item_name(self):
        return self.lambda_invocation_name
