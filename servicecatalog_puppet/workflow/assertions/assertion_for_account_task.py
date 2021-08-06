import luigi

from servicecatalog_puppet.workflow.assertions import assertion_for_task
from servicecatalog_puppet.workflow.generic import generic_for_account_task


class AssertionForAccountTask(generic_for_account_task.GenericForAccountTask, assertion_for_task.AssertionForTask):
    account_id = luigi.Parameter()
