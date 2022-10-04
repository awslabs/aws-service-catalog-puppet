#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet.workflow.dependencies import tasks


class CreateSpokeLocalPortfolioTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_task_reference = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            if self.puppet_account_id == self.account_id:
                spoke_portfolio = aws.find_portfolio(servicecatalog, self.portfolio)
            else:
                hub_portfolio_details = self.get_output_from_reference_dependency(
                    self.portfolio_task_reference
                )

                spoke_portfolio = aws.ensure_portfolio(
                    servicecatalog,
                    self.portfolio,
                    hub_portfolio_details.get("ProviderName"),
                    hub_portfolio_details.get("Description"),
                )
        self.write_output(spoke_portfolio)
