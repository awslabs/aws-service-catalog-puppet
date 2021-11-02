#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class DisassociateProductFromPortfolio(
    portfolio_management_task.PortfolioManagementTask
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio_id": self.portfolio_id,
            "product_id": self.product_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.disassociate_product_from_portfolio_{self.account_id}_{self.region}_{self.portfolio_id}_{self.product_id}": 1,
        }

    def run(self):
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            results = servicecatalog.disassociate_product_from_portfolio(
                PortfolioId=self.portfolio_id, ProductId=self.product_id,
            )
            self.write_output(results)
