#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import time

import luigi

from servicecatalog_puppet.workflow.launch import provisioning_task


class DoDescribeProvisioningParameters(provisioning_task.ProvisioningTask):
    puppet_account_id = luigi.Parameter()
    region = luigi.Parameter()
    product_id = luigi.Parameter()
    version_id = luigi.Parameter()
    portfolio = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product_id": self.product_id,
            "version_id": self.version_id,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.describe_provisioning_parameters_{self.puppet_account_id}_{self.region}",
        ]

    def run(self):
        with self.hub_regional_client("servicecatalog") as service_catalog:

            provisioning_artifact_parameters = None
            retries = 3
            while retries > 0:
                try:
                    provisioning_artifact_parameters = service_catalog.describe_provisioning_parameters(
                        ProductId=self.product_id,
                        ProvisioningArtifactId=self.version_id,
                        PathName=self.portfolio,
                    ).get(
                        "ProvisioningArtifactParameters", []
                    )
                    retries = 0
                    break
                except service_catalog.exceptions.ClientError as ex:
                    if "S3 error: Access Denied" in str(ex):
                        self.info("Swallowing S3 error: Access Denied")
                    else:
                        raise ex
                    time.sleep(3)
                    retries -= 1

            self.write_output(
                provisioning_artifact_parameters
                if isinstance(provisioning_artifact_parameters, list)
                else [provisioning_artifact_parameters]
            )
