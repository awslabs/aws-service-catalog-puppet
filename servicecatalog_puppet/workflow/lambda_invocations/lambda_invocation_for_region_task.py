import luigi

from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_for_task
from servicecatalog_puppet.workflow.generic import generic_for_region_task


class LambdaInvocationForRegionTask(
    generic_for_region_task.GenericForRegionTask,
    lambda_invocation_for_task.LambdaInvocationForTask,
):
    region = luigi.Parameter()
