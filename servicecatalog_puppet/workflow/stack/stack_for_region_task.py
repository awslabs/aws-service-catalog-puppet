import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.stack import stack_for_task


class StackForRegionTask(stack_for_task.StackForTask):
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "stack_name": self.stack_name,
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
            self.stack_name,
            self.region,
            single_account=self.single_account,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        stack = self.manifest.get(self.section_name).get(self.stack_name)
        for depends_on in stack.get("depends_on", []):
            if depends_on.get("type") == self.section_name:
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        self.__class__(
                            manifest_file_path=self.manifest_file_path,
                            stack_name=depends_on.get("name"),
                            puppet_account_id=self.puppet_account_id,
                            region=self.region,
                        )
                    )

        return requirements
