#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.portfolio.associations import (
    create_associations_in_python_for_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)
from servicecatalog_puppet.workflow.portfolio.sharing_management import (
    share_and_accept_portfolio_task,
)


class CreateShareForAccountLaunchRegion(
    portfolio_management_task.PortfolioManagementTask
):
    """for the given account_id and launch and region create the shares"""

    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    sharing_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "sharing_mode": self.sharing_mode,
            "account_id": self.account_id,
        }

    def requires(self):
        if self.account_id == self.puppet_account_id:
            return create_associations_in_python_for_portfolio_task.CreateAssociationsInPythonForPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
            )
        else:
            return share_and_accept_portfolio_task.ShareAndAcceptPortfolioTask(
                manifest_file_path=self.manifest_file_path,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                puppet_account_id=self.puppet_account_id,
                sharing_mode=self.sharing_mode,
            )

    def run(self):
        self.write_output(self.param_kwargs)
