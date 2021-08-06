import luigi

from servicecatalog_puppet.workflow.workspaces import workspace_for_task
from servicecatalog_puppet.workflow.generic import generic_for_account_task


class WorkspaceForAccountTask(generic_for_account_task.GenericForAccountTask, workspace_for_task.WorkspaceForTask):
    account_id = luigi.Parameter()
