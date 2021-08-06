import luigi

from servicecatalog_puppet.workflow.generic import generic_for_account_task
from servicecatalog_puppet.workflow.stack import stack_for_task


class StackForAccountTask(
    generic_for_account_task.GenericForAccountTask, stack_for_task.StackForTask
):
    account_id = luigi.Parameter()
