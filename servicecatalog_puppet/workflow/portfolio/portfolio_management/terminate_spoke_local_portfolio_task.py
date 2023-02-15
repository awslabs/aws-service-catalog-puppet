#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet.workflow.dependencies import tasks
from servicecatalog_puppet import constants


class TerminateSpokeLocalPortfolioTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_NORMAL

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "task_idempotency_token": self.task_idempotency_token,
        }

    def run(self):
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            if self.puppet_account_id == self.account_id:
                self.write_empty_output()
            else:
                portfolio = aws.find_portfolio(servicecatalog, self.portfolio)
                if portfolio is False:
                    self.write_empty_output()
                else:
                    servicecatalog.delete_portfolio(Id=portfolio.get("Id"))
                    self.write_empty_output()
