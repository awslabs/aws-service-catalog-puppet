#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.simulate_policies import simulate_policy_for_task
from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task


class SimulatePolicyForAccountAndRegionTask(
    generic_for_account_and_region_task.GenericForAccountAndRegionTask,
    simulate_policy_for_task.SimulatePolicyForTask,
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
