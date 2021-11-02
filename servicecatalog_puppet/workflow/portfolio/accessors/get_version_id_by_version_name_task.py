#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi

from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_product_id_by_product_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class GetVersionIdByVersionName(
    portfolio_management_task.PortfolioManagementTask, manifest_mixin.ManifestMixen
):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    product_id = None
    version_id = None

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product": self.product,
            "version": self.version,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
        ]

    def requires(self):
        if self.manifest.has_cache():
            if (
                self.manifest.get("id_cache")
                .get(self.region, {})
                .get(self.portfolio, {})
                .get("products", {})
                .get(self.product, {})
            ):
                product = self.manifest["id_cache"][self.region][self.portfolio][
                    "products"
                ][self.product]
                if product.get("versions", {}).get(str(self.version)):
                    self.product_id = product["id"]
                    self.version_id = product["versions"][self.version]
                    return []

        return dict(
            product=get_product_id_by_product_name_task.GetProductIdByProductName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                product=self.product,
                account_id=self.account_id,
                region=self.region,
            )
        )

    def run(self):
        if self.product_id is not None:
            product_id = self.product_id
            version_id = self.version_id
        else:
            details = self.load_from_input("product")
            product_id = details.get("product_id")
            with self.spoke_regional_client("servicecatalog") as servicecatalog:
                version_id = None
                response = servicecatalog.list_provisioning_artifacts_single_page(
                    ProductId=product_id,
                )
                for provisioning_artifact_detail in response.get(
                    "ProvisioningArtifactDetails"
                ):
                    if provisioning_artifact_detail.get("Name") == self.version:
                        version_id = provisioning_artifact_detail.get("Id")
                assert version_id is not None, "Did not find version looking for"

        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "version_name": self.version,
                        "version_id": version_id,
                        "product_name": self.product,
                        "product_id": product_id,
                    },
                    indent=4,
                    default=str,
                )
            )
