from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import provisioning as provisioning_tasks
from servicecatalog_puppet import constants


class LaunchSectionTask(manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        self.info(f"Launching and execution mode is: {self.execution_mode}")
        tasks = list()
        requirements = dict(tasks=tasks)
        if self.execution_mode == constants.EXECUTION_MODE_SPOKE:
            for launch_name, launch_details in self.manifest.get(
                "launches", {}
            ).items():
                if launch_details.get("execution") == constants.EXECUTION_MODE_SPOKE:
                    tasks.append(
                        provisioning_tasks.LaunchTask(
                            launch_name=launch_name,
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            should_use_product_plans=self.should_use_product_plans,
                            include_expanded_from=self.include_expanded_from,
                            single_account=self.single_account,
                            execution_mode=self.execution_mode,
                        )
                    )
        else:
            for launch_name, launch_details in self.manifest.get(
                "launches", {}
            ).items():
                if (
                    launch_details.get("execution") == constants.EXECUTION_MODE_SPOKE
                    and not self.is_dry_run
                ):
                    tasks.append(
                        provisioning_tasks.LaunchInSpokeTask(
                            launch_name=launch_name,
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            should_use_product_plans=self.should_use_product_plans,
                            include_expanded_from=self.include_expanded_from,
                            single_account=self.single_account,
                            execution_mode=self.execution_mode,
                        )
                    )
                else:
                    tasks.append(
                        provisioning_tasks.LaunchTask(
                            launch_name=launch_name,
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            should_use_product_plans=self.should_use_product_plans,
                            include_expanded_from=self.include_expanded_from,
                            single_account=self.single_account,
                            execution_mode=self.execution_mode,
                        )
                    )
        return requirements

    def run(self):
        self.write_output(self.manifest.get("launches", {}))
