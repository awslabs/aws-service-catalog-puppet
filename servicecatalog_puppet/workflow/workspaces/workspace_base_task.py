import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks as workflow_tasks


class WorkspaceBaseTask(workflow_tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.WORKSPACES

    @property
    def item_name(self):
        return self.workspace_name

    @property
    def item_identifier(self):
        return "workspace_name"
