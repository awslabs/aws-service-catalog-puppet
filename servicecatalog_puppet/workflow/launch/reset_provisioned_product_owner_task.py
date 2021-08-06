#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow.launch import provisioning_task


class ResetProvisionedProductOwnerTask(provisioning_task.ProvisioningTask):
    launch_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_properties_{self.account_id}_{self.region}",
        ]

    def run(self):
        self.info(f"starting ResetProvisionedProductOwnerTask")

        with self.spoke_regional_client("servicecatalog") as service_catalog:
            self.info(f"Checking if existing provisioned product exists")
            all_results = service_catalog.scan_provisioned_products_single_page(
                AccessLevelFilter={"Key": "Account", "Value": "self"},
            ).get("ProvisionedProducts", [])
            changes_made = list()
            for result in all_results:
                if result.get("Name") == self.launch_name:
                    provisioned_product_id = result.get("Id")
                    self.info(f"Ensuring current provisioned product owner is correct")
                    changes_made.append(result)
                    service_catalog.update_provisioned_product_properties(
                        ProvisionedProductId=provisioned_product_id,
                        ProvisionedProductProperties={
                            "OWNER": config.get_puppet_role_arn(self.account_id)
                        },
                    )
            self.write_output(changes_made)
