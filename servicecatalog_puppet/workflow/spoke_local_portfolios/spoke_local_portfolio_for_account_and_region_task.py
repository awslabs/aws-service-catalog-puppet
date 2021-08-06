#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_task,
)


class SpokeLocalPortfolioForAccountAndRegionTask(
    generic_for_account_and_region_task.GenericForAccountAndRegionTask,
    spoke_local_portfolio_for_task.SpokeLocalPortfolioForTask,
):
    region = luigi.Parameter()
    account_id = luigi.Parameter()
