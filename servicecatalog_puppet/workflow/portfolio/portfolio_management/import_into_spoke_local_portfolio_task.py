#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import time

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_products_and_provisioning_artifacts_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    create_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class ImportIntoSpokeLocalPortfolioTask(
    portfolio_management_task.PortfolioManagementTask
):
    spoke_local_portfolio_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    organization = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    sharing_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "create_spoke_local_portfolio": create_spoke_local_portfolio_task.CreateSpokeLocalPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                organization=self.organization,
                sharing_mode=self.sharing_mode,
            ),
            "products_and_provisioning_artifacts": get_products_and_provisioning_artifacts_task.GetProductsAndProvisioningArtifactsTask(
                manifest_file_path=self.manifest_file_path,
                region=self.region,
                portfolio=self.portfolio,
                puppet_account_id=self.puppet_account_id,
            ),
            "hub_portfolio": get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.puppet_account_id,
                region=self.region,
            ),
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
            f"servicecatalog.associate_product_with_portfolio_{self.account_id}_{self.region}",
        ]

    def run(self):
        with self.input().get("create_spoke_local_portfolio").open("r") as f:
            spoke_portfolio = json.loads(f.read())
        portfolio_id = spoke_portfolio.get("Id")

        with self.input().get("hub_portfolio").open("r") as f:
            hub_portfolio = json.loads(f.read())
        hub_portfolio_id = hub_portfolio.get("portfolio_id")

        product_name_to_id_dict = {}
        hub_product_to_import_list = []

        with self.input().get("products_and_provisioning_artifacts").open("r") as f:
            products_and_provisioning_artifacts = json.loads(f.read())
            for product_view_summary in products_and_provisioning_artifacts:
                hub_product_name = product_view_summary.get("Name")
                hub_product_id = product_view_summary.get("ProductId")
                product_name_to_id_dict[hub_product_name] = hub_product_id
                hub_product_to_import_list.append(hub_product_id)

        self.info(f"Starting product import with targets {hub_product_to_import_list}")

        with self.spoke_regional_client("servicecatalog") as spoke_service_catalog:

            while True:
                self.info(f"Generating product list for portfolio {portfolio_id}")

                response = spoke_service_catalog.search_products_as_admin_single_page(
                    PortfolioId=portfolio_id,
                )
                spoke_portfolio_products = [
                    product_view_detail.get("ProductViewSummary").get("ProductId")
                    for product_view_detail in response.get("ProductViewDetails")
                ]

                target_products = [
                    product_id
                    for product_id in hub_product_to_import_list
                    if product_id not in spoke_portfolio_products
                ]

                if not target_products:
                    self.info(
                        f"No more products for import to portfolio {portfolio_id}"
                    )
                    break

                self.info(
                    f"Products {target_products} not yet imported to portfolio {portfolio_id}"
                )

                for product_id in target_products:
                    self.info(f"Associating {product_id}")
                    spoke_service_catalog.associate_product_with_portfolio(
                        ProductId=product_id,
                        PortfolioId=portfolio_id,
                        SourcePortfolioId=hub_portfolio_id,
                    )

                # associate_product_with_portfolio is not a synchronous request
                # so wait a short time, then try again with any products not yet appeared
                time.sleep(2)

        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "portfolio": spoke_portfolio,
                        "products": product_name_to_id_dict,
                    },
                    indent=4,
                    default=str,
                )
            )
