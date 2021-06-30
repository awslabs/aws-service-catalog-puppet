import luigi

from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_for_task


class LambdaInvocationForRegionTask(lambda_invocation_for_task.LambdaInvocationForTask):
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        these_dependencies = list()
        requirements = dict(
            dependencies=dependencies, these_dependencies=these_dependencies,
        )

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
            self.puppet_account_id,
            self.section_name,
            self.lambda_invocation_name,
            self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
