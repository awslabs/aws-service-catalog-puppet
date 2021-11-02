#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class DeleteLocalPortfolio(portfolio_management_task.PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio_id": self.portfolio_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.delete_portfolio_{self.account_id}_{self.region}_{self.portfolio_id}": 1,
        }

    def run(self):
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            servicecatalog.delete_portfolio(Id=self.portfolio_id)
            self.write_output(self.params_for_results_display())
