#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi as luigi

from servicecatalog_puppet import utils
from servicecatalog_puppet.workflow.dependencies import tasks
from servicecatalog_puppet.workflow.general import delete_cloud_formation_stack_task


class TerminateLaunchRoleConstraintsForSpokeLocalPortfolioTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        stack_name = f"launch-constraints-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}"

        yield delete_cloud_formation_stack_task.DeleteCloudFormationStackTask(
            account_id=self.account_id,
            region=self.region,
            stack_name=stack_name,
            nonce=self.cache_invalidator,
        )

        self.write_output({})
