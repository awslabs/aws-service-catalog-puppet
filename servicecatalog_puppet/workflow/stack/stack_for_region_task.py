import luigi

from servicecatalog_puppet.workflow.stack import stack_for_task
from servicecatalog_puppet.workflow.generic import generic_for_region_task


class StackForRegionTask(
    generic_for_region_task.GenericForRegionTask, stack_for_task.StackForTask
):
    region = luigi.Parameter()
