import luigi

from servicecatalog_puppet.workflow.stack import stack_for_task


class StackForAccountAndRegionTask(stack_for_task.StackForTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "stack_name": self.stack_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_account_and_region(
            self.puppet_account_id,
            self.section_name,
            self.stack_name,
            self.account_id,
            self.region,
            single_account=self.single_account,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
