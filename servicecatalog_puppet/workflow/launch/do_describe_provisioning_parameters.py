#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import time

import luigi

from servicecatalog_puppet.workflow import tasks


class DoDescribeProvisioningParameters(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    region = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    portfolio = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product": self.product,
            "version": self.version,
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
                        ProductName=self.product,
                        ProvisioningArtifactName=self.version,
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
