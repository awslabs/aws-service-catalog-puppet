#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.simulate_policies import simulate_policy_base_task
from servicecatalog_puppet.workflow.simulate_policies import (
    do_execute_simulate_policy_task,
)
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class ExecuteSimulatePolicyTask(
    simulate_policy_base_task.SimulatePolicyBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    simulate_policy_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    execution = luigi.Parameter()

    requested_priority = luigi.IntParameter()

    simulation_type = luigi.Parameter()
    policy_source_arn = luigi.Parameter()
    policy_input_list = luigi.ListParameter()
    permissions_boundary_policy_input_list = luigi.ListParameter()
    action_names = luigi.ListParameter()
    expected_decision = luigi.Parameter()
    resource_arns = luigi.ListParameter()
    resource_policy = luigi.Parameter()
    resource_owner = luigi.Parameter()
    caller_arn = luigi.Parameter()
    context_entries = luigi.ListParameter()
    resource_handling_option = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "simulate_policy_name": self.simulate_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(section_dependencies=self.get_section_dependencies())

    def run(self):
        yield do_execute_simulate_policy_task.DoExecuteSimulatePolicyTask(
            manifest_file_path=self.manifest_file_path,
            simulate_policy_name=self.simulate_policy_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            account_id=self.account_id,
            simulation_type=self.simulation_type,
            policy_source_arn=self.policy_source_arn,
            policy_input_list=self.policy_input_list,
            permissions_boundary_policy_input_list=self.permissions_boundary_policy_input_list,
            action_names=self.action_names,
            expected_decision=self.expected_decision,
            resource_arns=self.resource_arns,
            resource_policy=self.resource_policy,
            resource_owner=self.resource_owner,
            caller_arn=self.caller_arn,
            context_entries=self.context_entries,
            resource_handling_option=self.resource_handling_option,
            requested_priority=self.requested_priority,
            execution=self.execution,
        )
        self.write_output(self.params_for_results_display())
