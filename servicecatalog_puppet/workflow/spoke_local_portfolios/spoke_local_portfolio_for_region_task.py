import luigi

from servicecatalog_puppet.workflow.generic import generic_for_region_task
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_task,
)


class SpokeLocalPortfolioForRegionTask(
    generic_for_region_task.GenericForRegionTask,
    spoke_local_portfolio_for_task.SpokeLocalPortfolioForTask,
):
    region = luigi.Parameter()
