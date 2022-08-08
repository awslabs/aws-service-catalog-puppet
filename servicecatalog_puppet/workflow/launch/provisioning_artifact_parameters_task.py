#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import time

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.launch import provisioning_task
from servicecatalog_puppet.workflow.portfolio.associations import (
    create_associations_in_python_for_portfolio_task,
)


class ProvisioningArtifactParametersTask(provisioning_task.ProvisioningTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product_name = luigi.Parameter()
    version_name = luigi.Parameter()
    region = luigi.Parameter()

    @property
    def retry_count(self):
        return 5

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product_name": self.product_name,
            "version_name": self.version_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.describe_provisioning_parameters_{self.puppet_account_id}_{self.region}",
        ]

    def requires(self):
        if self.execution_mode != constants.EXECUTION_MODE_SPOKE:
            return dict(
                associations=create_associations_in_python_for_portfolio_task.CreateAssociationsInPythonForPortfolioTask(
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                    account_id=self.puppet_account_id,
                    region=self.region,
                    portfolio=self.portfolio,
                )
            )
        else:
            return []

    def run(self):
        with self.hub_regional_client("servicecatalog") as service_catalog:
            provisioning_artifact_parameters = None
            retries = 3
            while retries > 0:
                try:
                    provisioning_artifact_parameters = service_catalog.describe_provisioning_parameters(
                        ProductName=self.product_name,
                        ProvisioningArtifactName=self.version_name,
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
