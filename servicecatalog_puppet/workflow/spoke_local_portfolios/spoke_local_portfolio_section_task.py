#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generic import generic_section_task
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_account_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_for_region_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_task,
)


class SpokeLocalPortfolioSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.SPOKE_LOCAL_PORTFOLIO
    section_name = constants.SPOKE_LOCAL_PORTFOLIOS
    for_region_task_klass = (
        spoke_local_portfolio_for_region_task.SpokeLocalPortfolioForRegionTask
    )
    for_account_task_klass = (
        spoke_local_portfolio_for_account_task.SpokeLocalPortfolioForAccountTask
    )
    for_account_and_region_task_klass = (
        spoke_local_portfolio_for_account_and_region_task.SpokeLocalPortfolioForAccountAndRegionTask
    )
    task_klass = spoke_local_portfolio_task.SpokeLocalPortfolioTask
    item_name = "spoke_local_portfolio_name"
    supports_spoke_mode = False
    supports_hub_and_spoke_split = True
