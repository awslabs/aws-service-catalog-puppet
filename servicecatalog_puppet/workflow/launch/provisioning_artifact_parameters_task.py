#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.launch import do_describe_provisioning_parameters
from servicecatalog_puppet.workflow.launch import provisioning_task
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_version_details_by_names_task,
)
from servicecatalog_puppet.workflow.portfolio.associations import (
    create_associations_in_python_for_portfolio_task,
)


class ProvisioningArtifactParametersTask(provisioning_task.ProvisioningTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()
    region = luigi.Parameter()

    @property
    def retry_count(self):
        return 5

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product": self.product,
            "version": self.version,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        required = dict(
            details=get_version_details_by_names_task.GetVersionDetailsByNames(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                product=self.product,
                version=self.version,
                account_id=self.single_account
                if self.execution_mode == constants.EXECUTION_MODE_SPOKE
                else self.puppet_account_id,
                region=self.region,
            ),
        )
        if self.execution_mode != constants.EXECUTION_MODE_SPOKE:
            required[
                "associations"
            ] = create_associations_in_python_for_portfolio_task.CreateAssociationsInPythonForPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.puppet_account_id,
                region=self.region,
                portfolio=self.portfolio,
            )
        return required

    def run(self):
        details = self.load_from_input("details")
        product_id = details.get("product_details").get("ProductId")
        version_id = details.get("version_details").get("Id")
        result = yield do_describe_provisioning_parameters.DoDescribeProvisioningParameters(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.single_account
            if self.execution_mode == constants.EXECUTION_MODE_SPOKE
            else self.puppet_account_id,
            region=self.region,
            product_id=product_id,
            version_id=version_id,
            portfolio=self.portfolio,
        )
        self.write_output(
            result.open("r").read(), skip_json_dump=True,
        )
