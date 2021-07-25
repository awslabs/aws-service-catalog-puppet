from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.manifest import section_task
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_account_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_region_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_task,
)


class SpokeLocalPortfolioSectionTask(section_task.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    def should_run(self):
        return (
            self.execution_mode == constants.EXECUTION_MODE_HUB and not self.is_dry_run
        )

    def requires(self):
        requirements = list()
        if self.should_run():

            for name, details in self.manifest.get(
                constants.SPOKE_LOCAL_PORTFOLIOS, {}
            ).items():
                requirements += self.handle_requirements_for(
                    name,
                    constants.SPOKE_LOCAL_PORTFOLIO,
                    constants.SPOKE_LOCAL_PORTFOLIOS,
                    spoke_local_portfolio_for_region_task.SpokeLocalPortfolioForRegionTask,
                    spoke_local_portfolio_for_account_task.SpokeLocalPortfolioForAccountTask,
                    spoke_local_portfolio_for_account_and_region_task.SpokeLocalPortfolioForAccountAndRegionTask,
                    spoke_local_portfolio_task.SpokeLocalPortfolioTask,
                    dict(
                        spoke_local_portfolio_name=name,
                        puppet_account_id=self.puppet_account_id,
                        manifest_file_path=self.manifest_file_path,
                    ),
                )

        return requirements

    def run(self):
        self.write_output(self.manifest.get("spoke-local-portfolios"))
