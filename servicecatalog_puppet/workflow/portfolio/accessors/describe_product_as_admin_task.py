#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class DescribeProductAsAdminTask(portfolio_management_task.PortfolioManagementTask):
    puppet_account_id = luigi.Parameter()
    product_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def api_calls_used(self):
        return [
            f"servicecatalog.describe_product_as_admin_{self.account_id}_{self.region}"
        ]

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "product_name": self.product_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):

        with self.spoke_regional_client("servicecatalog") as service_catalog:
            response = service_catalog.describe_product_as_admin(
                Name=self.product_name,
            )
            self.write_output(response)
