import luigi

from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_task


class WorkspaceForAccountAndRegionTask(
    generic_for_account_and_region_task.GenericForAccountAndRegionTask,
    workspace_for_task.WorkspaceForTask,
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
