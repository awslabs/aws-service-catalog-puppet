#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import time

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class AssociatePrincipalWithPortfolioTask(
    portfolio_management_task.PortfolioManagementTask
):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.associate_principal_with_portfolio_{self.region}": 1,
            f"servicecatalog.list_principals_for_portfolio_single_page_{self.region}": 1,
        }

    def run(self):
        p = f"data/associations/{self.region}/{self.portfolio}/"
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
        path = f"{p}/{self.account_id}.json"
        with open(path, "w") as f:
            f.write("{}")

        self.info(f"Creating the association for portfolio {self.portfolio_id}")
        principal_arn = config.get_puppet_role_arn(self.account_id)
        with self.hub_regional_client("servicecatalog") as servicecatalog:
            servicecatalog.associate_principal_with_portfolio(
                PortfolioId=self.portfolio_id,
                PrincipalARN=principal_arn,
                PrincipalType="IAM",
            )
            results = []
            needle = dict(PrincipalARN=principal_arn, PrincipalType="IAM")
            self.info(
                f"Checking for principal association of: {principal_arn} to: {self.portfolio_id}"
            )
            while needle not in results:
                self.info("- not found yet, still looking")
                time.sleep(1)
                results = servicecatalog.list_principals_for_portfolio_single_page(
                    PortfolioId=self.portfolio_id,
                ).get("Principals", [])

        self.write_output(self.param_kwargs)
