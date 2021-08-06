import luigi

from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task
from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_for_task


class LambdaInvocationForAccountAndRegionTask(
    generic_for_account_and_region_task.GenericForAccountAndRegionTask,
    lambda_invocation_for_task.LambdaInvocationForTask,
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
