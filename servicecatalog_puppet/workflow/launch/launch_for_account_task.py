import luigi

from servicecatalog_puppet.workflow.launch import launch_for_task


class LaunchForAccountTask(launch_for_task.LaunchForTask):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        account_launch_tasks = self.manifest.get_tasks_for_launch_and_account(
            self.puppet_account_id,
            self.section_name,
            self.launch_name,
            self.account_id,
            single_account=self.single_account,
        )
        for task in account_launch_tasks:
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
