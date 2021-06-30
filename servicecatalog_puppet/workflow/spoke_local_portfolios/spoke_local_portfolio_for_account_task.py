import luigi

from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_task,
)


class SpokeLocalPortfolioForAccountTask(
    spoke_local_portfolio_for_task.SpokeLocalPortfolioForTask
):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
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
            self.spoke_local_portfolio_name,
            self.account_id,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
