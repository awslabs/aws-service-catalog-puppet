#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks

sharing_mode_map = dict(ACCOUNT="IMPORTED", AWS_ORGANIZATIONS="AWS_ORGANIZATIONS",)


class GetPortfolioLocalTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    status = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_portfolio_details(self):
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            paginator = servicecatalog.get_paginator("list_portfolios")
            for page in paginator.paginate():
                for portfolio_details in page.get("PortfolioDetails", []):
                    if portfolio_details.get("DisplayName") == self.portfolio:
                        return portfolio_details
        if self.status == constants.TERMINATED:
            return {}
        else:
            raise Exception(f"Could not find portfolio: {self.portfolio}")

    def run(self):
        self.write_output(self.get_portfolio_details())


class GetPortfolioImportedTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    sharing_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "sharing_mode": self.sharing_mode,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_portfolio_details(self):
        mode = sharing_mode_map.get(self.sharing_mode)
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            paginator = servicecatalog.get_paginator("list_accepted_portfolio_shares")
            for page in paginator.paginate(PortfolioShareType=mode,):
                for portfolio_details in page.get("PortfolioDetails", []):
                    if portfolio_details.get("DisplayName") == self.portfolio:
                        return portfolio_details

        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            paginator = servicecatalog.get_paginator("list_accepted_portfolio_shares")
            for page in paginator.paginate(
                PortfolioShareType="IMPORTED"
                if mode == "AWS_ORGANIZATIONS"
                else "AWS_ORGANIZATIONS",
            ):
                for portfolio_details in page.get("PortfolioDetails", []):
                    if portfolio_details.get("DisplayName") == self.portfolio:
                        return portfolio_details

        raise Exception(f"Could not find portfolio: {self.portfolio}")

    def run(self):
        self.write_output(self.get_portfolio_details())
