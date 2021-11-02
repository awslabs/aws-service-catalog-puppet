#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class DeletePortfolioShare(portfolio_management_task.PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
            f"servicecatalog.delete_portfolio_share_{self.puppet_account_id}_{self.region}_{self.portfolio}",
        ]

    def run(self):
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            self.info(
                f"About to delete the portfolio share for: {self.portfolio} account: {self.account_id}"
            )
            result = servicecatalog.list_accepted_portfolio_shares_single_page()
            portfolio_id = None
            for portfolio_detail in result.get("PortfolioDetails", []):
                if portfolio_detail.get("DisplayName") == self.portfolio:
                    portfolio_id = portfolio_detail.get("Id")
                    break
        if portfolio_id:
            with self.hub_regional_client("servicecatalog") as servicecatalog:
                servicecatalog.delete_portfolio_share(
                    PortfolioId=portfolio_id, AccountId=self.account_id,
                )
        self.write_output(self.params_for_results_display())
