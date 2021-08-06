#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.associations import (
    associate_principal_with_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class CreateAssociationsInPythonForPortfolioTask(
    portfolio_management_task.PortfolioManagementTask
):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
        }

    def requires(self):
        return dict(
            portfolio=get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.account_id,
                region=self.region,
            )
        )

    def run(self):
        portfolio_details = self.load_from_input("portfolio")
        portfolio_id = portfolio_details.get("portfolio_id")

        yield associate_principal_with_portfolio_task.AssociatePrincipalWithPortfolioTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            portfolio_id=portfolio_id,
        )

        self.write_output(self.param_kwargs)
