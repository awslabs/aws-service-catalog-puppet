#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import copy
import json

import luigi
import yaml

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_products_and_provisioning_artifacts_task,
)


class GenerateManifestWithIdsTask(tasks.PuppetTask, manifest_mixin.ManifestMixen):
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = dict()
        regions = config.get_regions(self.puppet_account_id)
        for launch_name, launch_details in self.manifest.get_launches_items():
            portfolio = launch_details.get("portfolio")
            for region in regions:
                if requirements.get(region) is None:
                    requirements[region] = dict()

                regional_details = requirements[region]
                if regional_details.get(portfolio) is None:
                    regional_details[portfolio] = dict(products=dict())

                portfolio_details = regional_details[portfolio]
                if portfolio_details.get("details") is None:
                    portfolio_details[
                        "details"
                    ] = get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                        manifest_file_path=self.manifest_file_path,
                        portfolio=portfolio,
                        puppet_account_id=self.puppet_account_id,
                        account_id=self.puppet_account_id,
                        region=region,
                    )

                product = launch_details.get("product")
                products = portfolio_details.get("products")
                if products.get(product) is None:
                    products[
                        product
                    ] = get_products_and_provisioning_artifacts_task.GetProductsAndProvisioningArtifactsTask(
                        manifest_file_path=self.manifest_file_path,
                        region=region,
                        portfolio=portfolio,
                        puppet_account_id=self.puppet_account_id,
                    )
        return requirements

    def run(self):
        new_manifest = copy.deepcopy(self.manifest)
        regions = config.get_regions(self.puppet_account_id)
        global_id_cache = dict()
        new_manifest["id_cache"] = global_id_cache

        for region in regions:
            regional_id_cache = dict()
            r = self.input().get(region)
            for launch_name, launch_details in self.manifest.get_launches_items():
                target = r.get(launch_details.get("portfolio")).get("details")
                portfolio_id = json.loads(target.open("r").read()).get("portfolio_id")
                portfolio_name = launch_details.get("portfolio")
                if regional_id_cache.get(portfolio_name) is None:
                    regional_id_cache[portfolio_name] = dict(
                        id=portfolio_id, products=dict()
                    )

                product = launch_details.get("product")
                target = (
                    r.get(launch_details.get("portfolio")).get("products").get(product)
                )
                all_details = json.loads(target.open("r").read())
                all_products_and_their_versions = all_details
                for p in all_products_and_their_versions:
                    if (
                        regional_id_cache[portfolio_name]["products"].get(p.get("Name"))
                        is None
                    ):
                        regional_id_cache[portfolio_name]["products"][
                            p.get("Name")
                        ] = dict(id=p.get("ProductId"), versions=dict())

                    for a in p.get("provisioning_artifact_details"):
                        regional_id_cache[portfolio_name]["products"][p.get("Name")][
                            "versions"
                        ][a.get("Name")] = a.get("Id")

            global_id_cache[region] = regional_id_cache

        self.write_output(
            yaml.safe_dump(json.loads(json.dumps(new_manifest))), skip_json_dump=True
        )
