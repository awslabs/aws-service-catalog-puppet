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


class GetVersionDetailsByNames(portfolio_management_task.PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

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

    def requires(self):
        requirements = dict()

        if self.account_id == self.puppet_account_id:
            requirements[
                "details"
            ] = describe_product_as_admin_task.DescribeProductAsAdminTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                product=self.product,
                account_id=self.account_id,
                region=self.region,
            )
        else:
            requirements[
                "details"
            ] = get_version_id_by_version_name_task.GetVersionIdByVersionName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                product=self.product,
                version=self.version,
                account_id=self.account_id,
                region=self.region,
            )
            if not (
                self.execution_mode == constants.EXECUTION_MODE_SPOKE or self.is_dry_run
            ):
                requirements[
                    "generate_shares"
                ] = generate_shares_task.GenerateSharesTask(
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                    section=constants.LAUNCHES,
                )
        return requirements

    def run(self):
        details = self.load_from_input("details")

        if self.account_id == self.puppet_account_id:
            for provisioning_artifact_summary in details.get(
                "ProvisioningArtifactSummaries"
            ):
                if provisioning_artifact_summary.get("Name") == self.version:
                    self.write_output(
                        dict(
                            product_details=details.get("ProductViewDetail").get(
                                "ProductViewSummary"
                            ),
                            version_details=provisioning_artifact_summary,
                        )
                    )
                    return
        else:
            self.write_output(
                dict(
                    product_details=dict(ProductId=details.get("product_id")),
                    version_details=dict(Id=details.get("version_id")),
                )
            )
            return

        raise Exception(
            f"Could not find version: {self.version} of: {self.product} in: {self.portfolio}"
        )
