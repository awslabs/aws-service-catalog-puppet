from servicecatalog_puppet.workflow import provisioning as provisioning_tasks

from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import generate as generate_tasks


class SpokeLocalPortfolioSectionTask(manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
        }

    def requires(self):
        requirements = dict(
            manifest=manifest_tasks.ManifestTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
            )
        )

        if self.execution_mode == "hub":
            requirements.update(
                {
                    "generate_shares": generate_tasks.GenerateSharesTask(
                        manifest_file_path=self.manifest_file_path,
                        puppet_account_id=self.puppet_account_id,
                        should_use_sns=self.should_use_sns,
                        should_use_product_plans=self.should_use_product_plans,
                        include_expanded_from=self.include_expanded_from,
                        single_account=self.single_account,
                        is_dry_run=self.is_dry_run,
                        execution_mode=self.execution_mode,
                    ),
                }
            )
        return requirements

    def run(self):
        manifest = self.load_from_input("manifest")
        if self.execution_mode == "hub" and not self.is_dry_run:
            self.info("Generating sharing tasks")
            yield [
                provisioning_tasks.SpokeLocalPortfolioTask(
                    spoke_local_portfolio_name=spoke_local_portfolio_name,
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                    should_use_sns=self.should_use_sns,
                    should_use_product_plans=self.should_use_product_plans,
                    include_expanded_from=self.include_expanded_from,
                    single_account=self.single_account,
                    is_dry_run=self.is_dry_run,
                    depends_on=spoke_local_portfolio.get("depends_on", []),
                )
                for spoke_local_portfolio_name, spoke_local_portfolio in manifest.get(
                    "spoke-local-portfolios", {}
                ).items()
            ]
        self.write_output(manifest)
