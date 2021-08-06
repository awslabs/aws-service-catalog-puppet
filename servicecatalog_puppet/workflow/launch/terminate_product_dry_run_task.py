#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.launch import provisioning_task


class TerminateProductDryRunTask(provisioning_task.ProvisioningTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product = luigi.Parameter()
    product_id = luigi.Parameter()
    version = luigi.Parameter()
    version_id = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    retry_count = luigi.IntParameter(default=1)

    ssm_param_outputs = luigi.ListParameter(default=[])

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])

    try_count = 1

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def write_result(self, current_version, new_version, effect, notes=""):
        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "current_version": current_version,
                        "new_version": new_version,
                        "effect": effect,
                        "notes": notes,
                        "params": self.param_kwargs,
                    },
                    indent=4,
                    default=str,
                )
            )

    def api_calls_used(self):
        return [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",
        ]

    def run(self):
        self.info(
            f"starting dry run terminate try {self.try_count} of {self.retry_count}"
        )

        with self.spoke_regional_client("servicecatalog") as service_catalog:
            self.info(
                f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures"
            )
            r = aws.get_provisioned_product_details(
                self.product_id, self.launch_name, service_catalog
            )

            if r is None:
                self.write_result(
                    "-", "-", constants.NO_CHANGE, notes="There is nothing to terminate"
                )
            else:
                provisioned_product_name = (
                    service_catalog.describe_provisioning_artifact(
                        ProvisioningArtifactId=r.get("ProvisioningArtifactId"),
                        ProductId=self.product_id,
                    )
                    .get("ProvisioningArtifactDetail")
                    .get("Name")
                )

                if r.get("Status") != "TERMINATED":
                    self.write_result(
                        provisioned_product_name,
                        "-",
                        constants.CHANGE,
                        notes="The product would be terminated",
                    )
                else:
                    self.write_result(
                        "-",
                        "-",
                        constants.CHANGE,
                        notes="The product is already terminated",
                    )
