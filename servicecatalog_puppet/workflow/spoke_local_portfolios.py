from servicecatalog_puppet import constants, config
from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import provisioning as provisioning_tasks


class SpokeLocalPortfolioSectionTask(manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = dict()
        if self.execution_mode == constants.EXECUTION_MODE_HUB and not self.is_dry_run:
            requirements["spoke_local_portfolio_tasks"] = [
                provisioning_tasks.SpokeLocalPortfolioTask(
                    spoke_local_portfolio_name=spoke_local_portfolio_name,
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                    depends_on=spoke_local_portfolio.get("depends_on", []),
                    sharing_mode=spoke_local_portfolio.get(
                        "sharing_mode",
                        config.get_global_sharing_mode_default(self.puppet_account_id),
                    ),
                )
                for spoke_local_portfolio_name, spoke_local_portfolio in self.manifest.get(
                    "spoke-local-portfolios", {}
                ).items()
            ]

        return requirements

    def run(self):
        self.write_output(self.manifest.get("spoke-local-portfolios"))
