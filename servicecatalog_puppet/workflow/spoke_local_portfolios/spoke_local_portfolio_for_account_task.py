import luigi

from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_task,
)

from servicecatalog_puppet.workflow.generic import generic_for_account_task


class SpokeLocalPortfolioForAccountTask(
    generic_for_account_task.GenericForAccountTask,
    spoke_local_portfolio_for_task.SpokeLocalPortfolioForTask,
):
    account_id = luigi.Parameter()
