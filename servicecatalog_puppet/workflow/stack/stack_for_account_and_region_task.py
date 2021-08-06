import luigi

from servicecatalog_puppet.workflow.stack import stack_for_task

from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task

class StackForAccountAndRegionTask(generic_for_account_and_region_task.GenericForAccountAndRegionTask, stack_for_task.StackForTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
