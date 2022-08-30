#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class ImportIntoSpokeLocalPortfolioTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    portfolio_task_reference = luigi.Parameter()
    hub_portfolio_task_reference = luigi.Parameter()

    portfolio_get_all_products_and_their_versions_ref = luigi.Parameter()
    portfolio_get_all_products_and_their_versions_for_hub_ref = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
            f"servicecatalog.associate_product_with_portfolio_{self.account_id}_{self.region}",
        ]

    def run(self):
        spoke_portfolio_details = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_task_reference)
            .open("r")
            .read()
        )
        spoke_portfolio_id = spoke_portfolio_details.get("Id")
        spoke_products_and_their_versions = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_get_all_products_and_their_versions_ref)
            .open("r")
            .read()
        )
        hub_portfolio_details = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.hub_portfolio_task_reference)
            .open("r")
            .read()
        )
        hub_portfolio_id = hub_portfolio_details.get("Id")
        hub_products_and_their_versions = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_get_all_products_and_their_versions_for_hub_ref)
            .open("r")
            .read()
        )

        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            products_to_check = list()
            for (
                hub_product_name,
                hub_product_details,
            ) in hub_products_and_their_versions.items():
                if spoke_products_and_their_versions.get(hub_product_name) is None:
                    product_id = hub_product_details.get("ProductId")
                    self.info(f"Associating {product_id}")
                    servicecatalog.associate_product_with_portfolio(
                        ProductId=product_id,
                        PortfolioId=spoke_portfolio_id,
                        SourcePortfolioId=hub_portfolio_id,
                    )
                    products_to_check.append(product_id)

            n_products_to_check = len(products_to_check)
            products_found = 0
            while products_found < n_products_to_check:
                response = servicecatalog.search_products_as_admin_single_page(  # TODO optimise = swap for paginator
                    PortfolioId=spoke_portfolio_id,
                )
                products_ids = [
                    product_view_detail.get("ProductViewSummary").get("ProductId")
                    for product_view_detail in response.get("ProductViewDetails")
                ]
                products_found = 0
                for product_to_check in products_to_check:
                    if product_to_check in products_ids:
                        products_found += 1
            self.info("Finished waiting for association of products to portfolio")
            self.write_output({})
