#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoExecuteSimulatePolicyTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    execution = constants.EXECUTION_MODE_HUB
    requested_priority = 1

    puppet_account_id = "puppet_account_id"
    account_id = "account_id"
    region = "region"
    simulation_type = "principal"
    manifest_file_path = "manifest_file_path"
    simulate_policy_name = "simulate_policy_name"

    policy_source_arn = "policy_source_arn"
    policy_input_list = []
    permissions_boundary_policy_input_list = []
    action_names = []
    expected_decision = "expected_decision"
    resource_arns = []
    resource_policy = ""
    resource_owner = "resource_owner"
    caller_arn = "caller_arn"
    context_entries = []
    resource_handling_option = "resource_handling_option"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.simulate_policies import (
            do_execute_simulate_policy_task,
        )

        self.module = do_execute_simulate_policy_task

        self.sut = self.module.DoExecuteSimulatePolicyTask(
            manifest_file_path=self.manifest_file_path,
            simulate_policy_name=self.simulate_policy_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            account_id=self.account_id,
            execution=self.execution,
            requested_priority=self.requested_priority,
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
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "simulate_policy_name": self.simulate_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"iam.simulate_{self.simulation_type}_policy_{self.account_id}_{self.region}"
        ]

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
