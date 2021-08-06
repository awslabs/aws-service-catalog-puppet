#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    search_products_as_admin_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class GetProductIdByProductName(portfolio_management_task.PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product": self.product,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "search_products_as_admin": search_products_as_admin_task.SearchProductsAsAdminTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.account_id,
                region=self.region,
            ),
        }

    def run(self):
        product_id = None
        response = self.load_from_input("search_products_as_admin")
        for product_view_details in response.get("ProductViewDetails"):
            product_view = product_view_details.get("ProductViewSummary")
            self.info(f"looking at product: {product_view.get('Name')}")
            if product_view.get("Name") == self.product:
                self.info("Found product: {}".format(product_view))
                product_id = product_view.get("ProductId")
        assert product_id is not None, "Did not find product looking for"
        self.write_output(
            {
                "product_name": self.product,
                "product_id": product_id,
                "portfolio_name": self.portfolio,
            }
        )
