#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.simulate_policies import simulate_policy_base_task
from servicecatalog_puppet.workflow.simulate_policies import (
    execute_simulate_policy_task,
)
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class SimulatePolicyForTask(
    simulate_policy_base_task.SimulatePolicyBaseTask, manifest_mixin.ManifestMixen
):
    simulate_policy_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "simulate_policy_name": self.simulate_policy_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return execute_simulate_policy_task.ExecuteSimulatePolicyTask

    def run(self):
        self.write_output(self.params_for_results_display())
