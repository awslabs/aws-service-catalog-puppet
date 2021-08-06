#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.launch import provisioning_task


class ListLaunchPathsTask(provisioning_task.ProvisioningTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def api_calls_used(self):
        return [
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
        ]

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product_id": self.product_id,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        with self.hub_regional_client("servicecatalog") as service_catalog:
            self.info(f"Getting path for product {self.product_id}")
            response = service_catalog.list_launch_paths(ProductId=self.product_id)
            if len(response.get("LaunchPathSummaries")) == 1:
                path_id = response.get("LaunchPathSummaries")[0].get("Id")
                self.info(
                    f"There is only one path: {path_id} for product: {self.product_id}"
                )
                self.write_output(response.get("LaunchPathSummaries")[0])
            else:
                for launch_path_summary in response.get("LaunchPathSummaries", []):
                    name = launch_path_summary.get("Name")
                    if name == self.portfolio:
                        path_id = launch_path_summary.get("Id")
                        self.info(f"Got path: {path_id} for product: {self.product_id}")
                        self.write_output(launch_path_summary)
        raise Exception("Could not find a launch path")
