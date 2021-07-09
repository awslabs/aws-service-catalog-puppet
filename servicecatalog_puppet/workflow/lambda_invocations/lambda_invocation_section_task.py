from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_base_task,
)
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_for_account_task,
)
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_for_region_task,
)
from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_task
from servicecatalog_puppet.workflow.manifest import section_task


class LambdaInvocationsSectionTask(
    lambda_invocation_base_task.LambdaInvocationBaseTask, section_task.SectionTask
):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()

        for name, details in self.manifest.get(
            constants.LAMBDA_INVOCATIONS, {}
        ).items():
            requirements += self.handle_requirements_for(
                name,
                constants.LAMBDA_INVOCATION,
                constants.LAMBDA_INVOCATIONS,
                lambda_invocation_for_region_task.LambdaInvocationForRegionTask,
                lambda_invocation_for_account_task.LambdaInvocationForAccountTask,
                lambda_invocation_for_account_and_region_task.LambdaInvocationForAccountAndRegionTask,
                lambda_invocation_task.LambdaInvocationTask,
                dict(
                    lambda_invocation_name=name,
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                ),
            )
        return requirements

    def run(self):
        self.write_output(self.manifest.get("lambda-invocations"))
