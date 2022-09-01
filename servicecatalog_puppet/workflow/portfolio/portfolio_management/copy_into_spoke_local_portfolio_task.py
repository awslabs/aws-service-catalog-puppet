#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import time

import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class CopyIntoSpokeLocalPortfolioTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio_task_reference = luigi.Parameter()

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
            f"servicecatalog.copy_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_copy_product_status_{self.account_id}_{self.region}",
            f"servicecatalog.associate_product_with_portfolio_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioning_artifact_{self.account_id}_{self.region}",
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
        hub_products_and_their_versions = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_get_all_products_and_their_versions_for_hub_ref)
            .open("r")
            .read()
        )

        copy_product_tokens = list()
        versions_requiring_updates = dict()
        products_requiring_adding_to_portfolio = dict()
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            for (
                hub_product_name,
                hub_product_details,
            ) in hub_products_and_their_versions.items():
                versions_to_copy = list()
                args_to_use = dict(
                    SourceProductArn=hub_product_details.get("ProductArn"),
                    SourceProvisioningArtifactIdentifiers=versions_to_copy,
                    CopyOptions=["CopyTags",],
                )
                hub_versions_details = hub_product_details.get("Versions", {})
                if spoke_products_and_their_versions.get(hub_product_name):
                    args_to_use[
                        "TargetProductId"
                    ] = spoke_products_and_their_versions.get(hub_product_name).get(
                        "ProductId"
                    )
                else:
                    products_requiring_adding_to_portfolio[hub_product_name] = True

                spoke_product_details = spoke_products_and_their_versions.get(
                    hub_product_name, {}
                )
                spoke_versions_details = spoke_product_details.get("Versions", {})
                version_names_to_ignore = ["-"] + list(spoke_versions_details.keys())
                for (
                    hub_version_name,
                    hub_version_details,
                ) in hub_versions_details.items():
                    if hub_version_name not in version_names_to_ignore:
                        versions_to_copy.append(dict(Id=hub_version_details.get("Id"),))
                    else:
                        if hub_version_name == "-":
                            continue
                        spoke_product_id = spoke_product_details["ProductId"]
                        if not versions_requiring_updates.get(spoke_product_id):
                            versions_requiring_updates[spoke_product_id] = dict()
                        spoke_version_id = spoke_versions_details[hub_version_name][
                            "Id"
                        ]

                        versions_requiring_updates[spoke_product_id][
                            spoke_version_id
                        ] = dict(
                            Active=hub_version_details.get("Active"),
                            Guidance=hub_version_details.get("Guidance"),
                            Description=hub_version_details.get("Description"),
                        )

                if len(versions_to_copy) > 0:
                    copy_product_tokens.append(
                        (
                            hub_product_name,
                            servicecatalog.copy_product(**args_to_use).get(
                                "CopyProductToken"
                            ),
                        )
                    )
            self.info("Finished copying products")

            while len(copy_product_tokens) > 0:
                first_item_in_list = copy_product_tokens[0]
                product_name, copy_product_token_to_check = first_item_in_list
                response = servicecatalog.describe_copy_product_status(
                    CopyProductToken=copy_product_token_to_check
                )
                copy_product_status = response.get("CopyProductStatus")
                if copy_product_status == "SUCCEEDED":
                    if products_requiring_adding_to_portfolio.get(product_name):
                        products_requiring_adding_to_portfolio[
                            product_name
                        ] = response.get("TargetProductId")
                    copy_product_tokens.remove(first_item_in_list)
                elif copy_product_status == "FAILED":
                    raise Exception(f"Failed to copy product {copy_product_status}")
                elif copy_product_status == "IN_PROGRESS":
                    time.sleep(1)
                else:
                    raise Exception(f"Not handled copy product status {response}")
        self.info("Finished waiting for copy products")

        for product_name, product_id in products_requiring_adding_to_portfolio.items():
            servicecatalog.associate_product_with_portfolio(
                ProductId=product_id, PortfolioId=spoke_portfolio_id,
            )
        self.info("Finished associating products")

        for product_id, product_details in versions_requiring_updates.items():
            for version_id, version_details in product_details.items():
                servicecatalog.update_provisioning_artifact(
                    ProductId=product_id,
                    ProvisioningArtifactId=version_id,
                    **version_details,
                )
        self.info("Finished updating versions that were copied")

        products_to_check = list(products_requiring_adding_to_portfolio.values())
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
