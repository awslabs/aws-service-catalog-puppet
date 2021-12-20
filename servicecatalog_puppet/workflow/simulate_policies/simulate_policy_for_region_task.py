#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.simulate_policies import simulate_policy_for_task
from servicecatalog_puppet.workflow.generic import generic_for_region_task


class SimulatePolicyForRegionTask(
    generic_for_region_task.GenericForRegionTask,
    simulate_policy_for_task.SimulatePolicyForTask,
):
    region = luigi.Parameter()
