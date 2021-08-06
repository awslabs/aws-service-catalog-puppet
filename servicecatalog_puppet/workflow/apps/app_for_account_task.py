import luigi
from servicecatalog_puppet.workflow.apps import app_for_task
from servicecatalog_puppet.workflow.generic import generic_for_account_task


class AppForAccountTask(
    generic_for_account_task.GenericForAccountTask, app_for_task.AppForTask
):
    account_id = luigi.Parameter()
