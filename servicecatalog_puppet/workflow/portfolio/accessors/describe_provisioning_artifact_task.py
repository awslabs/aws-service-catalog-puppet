#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generate import generate_shares_task
from servicecatalog_puppet.workflow.portfolio.accessors import (
    describe_product_as_admin_task,
)
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_version_id_by_version_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class DescribeProvisioningArtifactTask(
    portfolio_management_task.PortfolioManagementTask
):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product_name = luigi.Parameter()
    version_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product_name": self.product_name,
            "version_name": self.version_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        uniq = f"{self.account_id}_{self.region}"

        return [f"servicecatalog.describe_provisioning_artifact_{uniq}"]

    def run(self):
        if self.account_id != self.puppet_account_id:
            raise Exception("Not yet implemented")

        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            provisioning_artifact_detail = servicecatalog.describe_provisioning_artifact(
                ProductName=self.product_name,
                ProvisioningArtifactName=self.version_name,
            ).get(
                "ProvisioningArtifactDetail"
            )

        self.write_output(provisioning_artifact_detail)
