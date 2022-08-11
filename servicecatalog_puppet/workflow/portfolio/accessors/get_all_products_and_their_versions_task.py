#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from servicecatalog_puppet.workflow import tasks

import luigi
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)


class GetAllProductsAndTheirVersionsTask(tasks.PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    portfolio_task_reference = luigi.Parameter()

    task_reference = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(
            reference_dependencies=get_dependencies_for_task_reference(
                self.manifest_task_reference_file_path,
                self.task_reference,
                self.puppet_account_id,
            )
        )

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.describe_product_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.describe_product_as_admin_{self.account_id}_{self.region}",
        ]

    def run(self):
        portfolio_details = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_task_reference)
            .open("r")
            .read()
        )
        portfolio_id = portfolio_details.get("Id")

        products = dict()
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            paginator = servicecatalog.get_paginator("search_products_as_admin")
            for page in paginator.paginate(
                PortfolioId=portfolio_id, ProductSource="ACCOUNT",
            ):
                for product_view_detail in page.get("ProductViewDetails", []):
                    product_arn = product_view_detail.get("ProductARN")
                    product_view_summary = product_view_detail.get("ProductViewSummary")
                    product_view_summary["ProductArn"] = product_arn
                    product_view_summary["Versions"] = dict()
                    product_id = product_view_summary.get("ProductId")
                    product_name = product_view_summary.get("Name")
                    products[product_name] = product_view_summary
                    provisioning_artifact_summaries = servicecatalog.describe_product_as_admin(
                        Id=product_view_summary.get("ProductId"),
                    ).get(
                        "ProvisioningArtifactSummaries"
                    )
                    for (
                        provisioning_artifact_summary
                    ) in provisioning_artifact_summaries:
                        version_name = provisioning_artifact_summary.get("Name")
                        provisioning_artifact_detail = servicecatalog.describe_provisioning_artifact(
                            ProductId=product_id, ProvisioningArtifactName=version_name,
                        ).get(
                            "ProvisioningArtifactDetail"
                        )
                        provisioning_artifact_summary[
                            "Active"
                        ] = provisioning_artifact_detail.get("Active")
                        provisioning_artifact_summary[
                            "Guidance"
                        ] = provisioning_artifact_detail.get("Guidance")
                        product_view_summary["Versions"][
                            version_name
                        ] = provisioning_artifact_summary
        self.write_output(products)
