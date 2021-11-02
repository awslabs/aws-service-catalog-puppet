#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class GetPortfolioByPortfolioName(
    portfolio_management_task.PortfolioManagementTask, manifest_mixin.ManifestMixen
):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        if self.manifest.has_cache() and self.manifest.get("id_cache").get(
            self.region, {}
        ).get(self.portfolio, {}).get("id"):
            return []
        else:
            return [
                f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
                f"servicecatalog.list_portfolios_{self.account_id}_{self.region}",
            ]

    def run(self):
        if self.manifest.has_cache() and self.manifest.get("id_cache").get(
            self.region, {}
        ).get(self.portfolio, {}).get("id"):
            self.write_output(
                {
                    "portfolio_name": self.portfolio,
                    "portfolio_id": self.manifest["id_cache"][self.region][
                        self.portfolio
                    ]["id"],
                    "provider_name": "not set",
                    "description": "not set",
                }
            )
        else:
            with self.spoke_regional_client(
                "servicecatalog"
            ) as cross_account_servicecatalog:
                result = None
                response = cross_account_servicecatalog.list_accepted_portfolio_shares_single_page(
                    PortfolioShareType="AWS_ORGANIZATIONS"
                )
                for portfolio_detail in response.get("PortfolioDetails"):
                    if portfolio_detail.get("DisplayName") == self.portfolio:
                        result = portfolio_detail
                        break

                if result is None:
                    response = (
                        cross_account_servicecatalog.list_portfolios_single_page()
                    )
                    for portfolio_detail in response.get("PortfolioDetails", []):
                        if portfolio_detail.get("DisplayName") == self.portfolio:
                            result = portfolio_detail
                            break

                assert result is not None, "Could not find portfolio"
            self.write_output(
                {
                    "portfolio_name": self.portfolio,
                    "portfolio_id": result.get("Id"),
                    "provider_name": result.get("ProviderName"),
                    "description": result.get("Description"),
                }
            )
