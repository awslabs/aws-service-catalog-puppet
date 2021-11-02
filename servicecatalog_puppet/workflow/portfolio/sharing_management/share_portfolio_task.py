#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class SharePortfolioTask(portfolio_management_task.PortfolioManagementTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(
            portfolio=get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.puppet_account_id,
                region=self.region,
            )
        )

    def api_calls_used(self):
        return [
            f"servicecatalog.list_portfolio_access_single_page_{self.region}",
            f"servicecatalog.create_portfolio_share_{self.region}",
        ]

    def run(self):
        portfolio = self.load_from_input("portfolio")
        portfolio_id = portfolio.get("portfolio_id")

        p = f"data/shares/{self.region}/{self.portfolio}/"
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        path = f"{p}/{self.account_id}.json"
        with open(path, "w") as f:
            f.write("{}")

        self.info(f"{self.uid}: checking {portfolio_id} with {self.account_id}")
        with self.hub_regional_client("servicecatalog") as servicecatalog:
            account_ids = servicecatalog.list_portfolio_access_single_page(
                PortfolioId=portfolio_id, PageSize=20,
            ).get("AccountIds")

            if self.account_id in account_ids:
                self.info(
                    f"{self.uid}: not sharing {portfolio_id} with {self.account_id} as was previously shared"
                )
            else:
                self.info(f"{self.uid}: sharing {portfolio_id} with {self.account_id}")
                servicecatalog.create_portfolio_share(
                    PortfolioId=portfolio_id, AccountId=self.account_id,
                )
        self.write_output(self.param_kwargs)
