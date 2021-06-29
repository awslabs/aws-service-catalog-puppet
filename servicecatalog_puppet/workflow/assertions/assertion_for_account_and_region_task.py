import luigi

from servicecatalog_puppet.workflow.assertions import assertion_for_task


class AssertionForAccountAndRegionTask(assertion_for_task.AssertionForTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_account_and_region(
            self.puppet_account_id,
            self.section_name,
            self.assertion_name,
            self.account_id,
            self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
