#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks
from servicecatalog_puppet.workflow.portfolio.associations import association_utils


class TerminateAssociationsForSpokeLocalPortfolioTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "region": self.region,
            "account_id": self.account_id,
        }

    def run(self):
        stack_name = association_utils.generate_stack_name_for_associations_by_item_name(
            self.spoke_local_portfolio_name
        )

        with self.spoke_regional_client("cloudformation") as cloudformation:
            self.info(f"About to delete the stack: {stack_name}")
            cloudformation.ensure_deleted(StackName=stack_name)
        self.write_empty_output()
