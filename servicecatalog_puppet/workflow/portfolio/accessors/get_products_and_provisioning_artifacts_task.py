#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    search_products_as_admin_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class GetProductsAndProvisioningArtifactsTask(
    portfolio_management_task.PortfolioManagementTask
):
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "search_products_as_admin": search_products_as_admin_task.SearchProductsAsAdminTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                region=self.region,
                account_id=self.puppet_account_id,
            )
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_provisioning_artifacts_{self.puppet_account_id}_{self.region}",
        ]

    def run(self):
        product_and_artifact_details = []
        with self.hub_regional_client("servicecatalog") as service_catalog:
            response = self.load_from_input("search_products_as_admin")
            for product_view_detail in response.get("ProductViewDetails", []):
                product_view_summary = product_view_detail.get("ProductViewSummary")
                product_view_summary["ProductARN"] = product_view_detail.get(
                    "ProductARN"
                )
                product_and_artifact_details.append(product_view_summary)

                provisioning_artifact_details = product_view_summary[
                    "provisioning_artifact_details"
                ] = []
                hub_product_id = product_view_summary.get("ProductId")
                hub_provisioning_artifact_details = service_catalog.list_provisioning_artifacts(
                    ProductId=hub_product_id
                ).get(
                    "ProvisioningArtifactDetails", []
                )
                for (
                    hub_provisioning_artifact_detail
                ) in hub_provisioning_artifact_details:
                    if (
                        hub_provisioning_artifact_detail.get("Type")
                        == "CLOUD_FORMATION_TEMPLATE"
                    ):
                        provisioning_artifact_details.append(
                            hub_provisioning_artifact_detail
                        )

        self.write_output(product_and_artifact_details)
