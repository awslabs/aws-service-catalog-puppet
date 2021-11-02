#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class SearchProductsAsAdminTask(portfolio_management_task.PortfolioManagementTask):
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

    def requires(self):
        return dict(
            portfolio=get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.account_id,
                region=self.region,
            )
        )

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
        ]

    def run(self):
        portfolio_details = self.load_from_input("portfolio")
        with self.spoke_regional_client("servicecatalog") as spoke_service_catalog:
            results = spoke_service_catalog.search_products_as_admin_single_page(
                PortfolioId=portfolio_details.get("portfolio_id"),
            )
            self.write_output(results)
