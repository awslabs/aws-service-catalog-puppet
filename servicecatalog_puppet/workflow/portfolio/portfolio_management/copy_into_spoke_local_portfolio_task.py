#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import time

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_products_and_provisioning_artifacts_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    create_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class CopyIntoSpokeLocalPortfolioTask(
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
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                organization=self.organization,
                puppet_account_id=self.puppet_account_id,
                sharing_mode=self.sharing_mode,
            ),
            "products_and_provisioning_artifacts": get_products_and_provisioning_artifacts_task.GetProductsAndProvisioningArtifactsTask(
                manifest_file_path=self.manifest_file_path,
                region=self.region,
                portfolio=self.portfolio,
                puppet_account_id=self.puppet_account_id,
            ),
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
            f"servicecatalog.copy_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_copy_product_status_{self.account_id}_{self.region}",
            f"servicecatalog.associate_product_with_portfolio_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioning_artifact_{self.account_id}_{self.region}",
        ]

    def run(self):
        with self.input().get("create_spoke_local_portfolio").open("r") as f:
            spoke_portfolio = json.loads(f.read())
        portfolio_id = spoke_portfolio.get("Id")
        product_versions_that_should_be_copied = {}
        product_versions_that_should_be_updated = {}

        product_name_to_id_dict = {}
        with self.input().get("products_and_provisioning_artifacts").open("r") as f:
            products_and_provisioning_artifacts = json.loads(f.read())
            for product_view_summary in products_and_provisioning_artifacts:
                spoke_product_id = False
                target_product_id = False
                hub_product_name = product_view_summary.get("Name")

                for hub_provisioning_artifact_detail in product_view_summary.get(
                    "provisioning_artifact_details", []
                ):
                    if (
                        hub_provisioning_artifact_detail.get("Type")
                        == "CLOUD_FORMATION_TEMPLATE"
                    ):
                        product_versions_that_should_be_copied[
                            f"{hub_provisioning_artifact_detail.get('Name')}"
                        ] = hub_provisioning_artifact_detail
                        product_versions_that_should_be_updated[
                            f"{hub_provisioning_artifact_detail.get('Name')}"
                        ] = hub_provisioning_artifact_detail

                self.info(f"Copying {hub_product_name}")
                hub_product_arn = product_view_summary.get("ProductARN")
                copy_args = {
                    "SourceProductArn": hub_product_arn,
                    "CopyOptions": ["CopyTags",],
                }

                with self.spoke_regional_client(
                    "servicecatalog"
                ) as spoke_service_catalog:
                    p = None
                    try:
                        p = spoke_service_catalog.search_products_as_admin_single_page(
                            PortfolioId=portfolio_id,
                            Filters={"FullTextSearch": [hub_product_name]},
                        )
                    except spoke_service_catalog.exceptions.ResourceNotFoundException as e:
                        self.info(f"swallowing exception: {str(e)}")

                    if p is not None:
                        for spoke_product_view_details in p.get("ProductViewDetails"):
                            spoke_product_view = spoke_product_view_details.get(
                                "ProductViewSummary"
                            )
                            if spoke_product_view.get("Name") == hub_product_name:
                                spoke_product_id = spoke_product_view.get("ProductId")
                                product_name_to_id_dict[
                                    hub_product_name
                                ] = spoke_product_id
                                copy_args["TargetProductId"] = spoke_product_id
                                spoke_provisioning_artifact_details = spoke_service_catalog.list_provisioning_artifacts(
                                    ProductId=spoke_product_id
                                ).get(
                                    "ProvisioningArtifactDetails"
                                )
                                for (
                                    provisioning_artifact_detail
                                ) in spoke_provisioning_artifact_details:
                                    id_to_delete = (
                                        f"{provisioning_artifact_detail.get('Name')}"
                                    )
                                    if (
                                        product_versions_that_should_be_copied.get(
                                            id_to_delete, None
                                        )
                                        is not None
                                    ):
                                        self.info(
                                            f"{hub_product_name} :: Going to skip {spoke_product_id} {provisioning_artifact_detail.get('Name')}"
                                        )
                                        del product_versions_that_should_be_copied[
                                            id_to_delete
                                        ]

                    if len(product_versions_that_should_be_copied.keys()) == 0:
                        self.info(f"no versions to copy")
                    else:
                        self.info(f"about to copy product")

                        copy_args["SourceProvisioningArtifactIdentifiers"] = [
                            {"Id": a.get("Id")}
                            for a in product_versions_that_should_be_copied.values()
                        ]

                        self.info(f"about to copy product with args: {copy_args}")
                        copy_product_token = spoke_service_catalog.copy_product(
                            **copy_args
                        ).get("CopyProductToken")
                        while True:
                            time.sleep(5)
                            r = spoke_service_catalog.describe_copy_product_status(
                                CopyProductToken=copy_product_token
                            )
                            target_product_id = r.get("TargetProductId")
                            self.info(
                                f"{hub_product_name} status: {r.get('CopyProductStatus')}"
                            )
                            if r.get("CopyProductStatus") == "FAILED":
                                raise Exception(
                                    f"Copying "
                                    f"{hub_product_name} failed: {r.get('StatusDetail')}"
                                )
                            elif r.get("CopyProductStatus") == "SUCCEEDED":
                                break

                        self.info(
                            f"adding {target_product_id} to portfolio {portfolio_id}"
                        )
                        spoke_service_catalog.associate_product_with_portfolio(
                            ProductId=target_product_id, PortfolioId=portfolio_id,
                        )

                        # associate_product_with_portfolio is not a synchronous request
                        self.info(
                            f"waiting for adding of {target_product_id} to portfolio {portfolio_id}"
                        )
                        while True:
                            time.sleep(2)
                            response = spoke_service_catalog.search_products_as_admin_single_page(
                                PortfolioId=portfolio_id,
                            )
                            products_ids = [
                                product_view_detail.get("ProductViewSummary").get(
                                    "ProductId"
                                )
                                for product_view_detail in response.get(
                                    "ProductViewDetails"
                                )
                            ]
                            self.info(
                                f"Looking for {target_product_id} in {products_ids}"
                            )

                            if target_product_id in products_ids:
                                break

                        product_name_to_id_dict[hub_product_name] = target_product_id

                    product_id_in_spoke = spoke_product_id or target_product_id
                    spoke_provisioning_artifact_details = spoke_service_catalog.list_provisioning_artifacts(
                        ProductId=product_id_in_spoke
                    ).get(
                        "ProvisioningArtifactDetails", []
                    )
                    for (
                        version_name,
                        version_details,
                    ) in product_versions_that_should_be_updated.items():
                        self.info(
                            f"{version_name} is active: {version_details.get('Active')} in hub"
                        )
                        for (
                            spoke_provisioning_artifact_detail
                        ) in spoke_provisioning_artifact_details:
                            if (
                                spoke_provisioning_artifact_detail.get("Name")
                                == version_name
                            ):
                                self.info(
                                    f"Updating active of {version_name}/{spoke_provisioning_artifact_detail.get('Id')} "
                                    f"in the spoke to {version_details.get('Active')}"
                                )
                                spoke_service_catalog.update_provisioning_artifact(
                                    ProductId=product_id_in_spoke,
                                    ProvisioningArtifactId=spoke_provisioning_artifact_detail.get(
                                        "Id"
                                    ),
                                    Active=version_details.get("Active"),
                                )

        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "portfolio": spoke_portfolio,
                        "product_versions_that_should_be_copied": product_versions_that_should_be_copied,
                        "products": product_name_to_id_dict,
                    },
                    indent=4,
                    default=str,
                )
            )
