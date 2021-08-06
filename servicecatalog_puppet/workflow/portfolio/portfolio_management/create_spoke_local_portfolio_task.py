#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)
from servicecatalog_puppet.workflow.portfolio.sharing_management import (
    create_share_for_account_launch_region_task,
)


class CreateSpokeLocalPortfolioTask(
    portfolio_management_task.PortfolioManagementTask, manifest_mixin.ManifestMixen
):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    organization = luigi.Parameter(significant=False)
    sharing_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "create_share_for_account_launch_region": create_share_for_account_launch_region_task.CreateShareForAccountLaunchRegion(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.account_id,
                region=self.region,
                sharing_mode=self.sharing_mode,
            ),
            "puppet_portfolio": get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.puppet_account_id,
                region=self.region,
            ),
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_portfolios_{self.account_id}_{self.region}",
            f"servicecatalog.create_portfolio_{self.account_id}_{self.region}",
        ]

    def run(self):
        with self.input().get("puppet_portfolio").open("r") as f:
            portfolio_details = json.loads(f.read())
        with self.spoke_regional_client("servicecatalog") as spoke_service_catalog:
            spoke_portfolio = aws.ensure_portfolio(
                spoke_service_catalog,
                self.portfolio,
                portfolio_details.get("provider_name"),
                portfolio_details.get("description"),
            )
        self.write_output(spoke_portfolio)
