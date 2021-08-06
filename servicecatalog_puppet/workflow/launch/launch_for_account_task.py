import luigi

from servicecatalog_puppet.workflow.launch import launch_for_task
from servicecatalog_puppet.workflow.generic import generic_for_account_task


class LaunchForAccountTask(
    generic_for_account_task.GenericForAccountTask, launch_for_task.LaunchForTask
):
    account_id = luigi.Parameter()
