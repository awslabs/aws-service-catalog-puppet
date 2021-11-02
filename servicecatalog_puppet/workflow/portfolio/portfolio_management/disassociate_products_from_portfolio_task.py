#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    disassociate_product_from_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class DisassociateProductsFromPortfolio(
    portfolio_management_task.PortfolioManagementTask
):
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
            f"servicecatalog.search_products_as_admin_single_page_{self.account_id}_{self.region}_{self.portfolio_id}": 1,
        }

    def requires(self):
        disassociates = list()
        requirements = dict(disassociates=disassociates)
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            results = servicecatalog.search_products_as_admin_single_page(
                PortfolioId=self.portfolio_id
            )
            for product_view_detail in results.get("ProductViewDetails", []):
                disassociates.append(
                    disassociate_product_from_portfolio_task.DisassociateProductFromPortfolio(
                        account_id=self.account_id,
                        region=self.region,
                        portfolio_id=self.portfolio_id,
                        product_id=product_view_detail.get("ProductViewSummary").get(
                            "ProductId"
                        ),
                        manifest_file_path=self.manifest_file_path,
                    )
                )
        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())
