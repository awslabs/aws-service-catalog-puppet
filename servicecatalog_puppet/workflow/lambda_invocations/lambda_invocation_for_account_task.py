import luigi

from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_for_task


class LambdaInvocationForAccountTask(
    lambda_invocation_for_task.LambdaInvocationForTask
):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
            self.puppet_account_id,
            self.section_name,
            self.lambda_invocation_name,
            self.account_id,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
