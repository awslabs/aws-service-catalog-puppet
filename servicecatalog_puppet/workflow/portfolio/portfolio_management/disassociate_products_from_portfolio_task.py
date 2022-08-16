#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)

from servicecatalog_puppet.workflow.dependencies import tasks


class DisassociateProductsFromPortfolio(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_task_reference = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.disassociate_product_from_portfolio_{self.account_id}_{self.region}": 1,
        }

    def run(self):
        portfolio = self.get_output_from_reference_dependency(
            self.portfolio_task_reference
        )
        portfolio_id = portfolio.get("Id")

        if portfolio_id is None:
            self.write_output(list())
            return
        else:
            disassociations = list()
            with self.spoke_regional_client("servicecatalog") as servicecatalog:
                paginator = servicecatalog.get_paginator("search_products_as_admin")
                for page in paginator.paginate(PortfolioId=portfolio_id):
                    for product_view_details in page.get("ProductViewDetails", []):
                        product_id = product_view_details.get(
                            "ProductViewSummary", {}
                        ).get("ProductId")
                        servicecatalog.disassociate_product_from_portfolio(
                            PortfolioId=portfolio_id, ProductId=product_id,
                        )
                        disassociations.append(
                            dict(portfolio_id=portfolio_id, product_id=product_id)
                        )

            self.write_output(disassociations)
