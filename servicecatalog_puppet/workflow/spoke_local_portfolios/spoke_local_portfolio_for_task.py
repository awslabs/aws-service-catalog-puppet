#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    share_portfolio_with_spoke_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_base_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    terminate_portfolio_in_spoke_task,
)


class SpokeLocalPortfolioForTask(
    spoke_local_portfolio_base_task.SpokeLocalPortfolioBaseTask,
    manifest_mixin.ManifestMixen,
):
    spoke_local_portfolio_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        raise NotImplementedError()

    def get_klass_for_provisioning(self):
        if self.status == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED:
            return share_portfolio_with_spoke_task.SharePortfolioWithSpokeTask
        elif self.status == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED:
            return terminate_portfolio_in_spoke_task.TerminatePortfolioInSpokeTask
        else:
            raise Exception(f"Unknown status: {self.status}")

    def run(self):
        self.write_output(self.params_for_results_display())
