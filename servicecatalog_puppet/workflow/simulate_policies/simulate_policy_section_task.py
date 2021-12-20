#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.simulate_policies import (
    simulate_policy_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.simulate_policies import (
    simulate_policy_for_account_task,
)
from servicecatalog_puppet.workflow.simulate_policies import (
    simulate_policy_for_region_task,
)
from servicecatalog_puppet.workflow.simulate_policies import simulate_policy_task

from servicecatalog_puppet.workflow.generic import generic_section_task


class SimulatePolicysSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.SIMULATE_POLICY
    section_name = constants.SIMULATE_POLICIES
    for_region_task_klass = simulate_policy_for_region_task.SimulatePolicyForRegionTask
    for_account_task_klass = (
        simulate_policy_for_account_task.SimulatePolicyForAccountTask
    )
    for_account_and_region_task_klass = (
        simulate_policy_for_account_and_region_task.SimulatePolicyForAccountAndRegionTask
    )
    task_klass = simulate_policy_task.SimulatePolicyTask
    item_name = "simulate_policy_name"
    supports_spoke_mode = True
