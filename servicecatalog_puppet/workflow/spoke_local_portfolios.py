from servicecatalog_puppet.workflow import provisioning as provisioning_tasks

from servicecatalog_puppet.workflow import manifest as manifest_tasks


class SpokeLocalPortfolioSectionTask(manifest_tasks.SectionTask):
    def run(self):
        manifest = self.load_from_input('manifest')

        if not self.is_dry_run:
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
                ) for spoke_local_portfolio_name in manifest.get('spoke-local-portfolios', {}).keys()
            ]
        self.write_output(manifest)
