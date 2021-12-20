#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoExecuteServiceControlPoliciesTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    manifest_file_path = "manifest_file_path"

    service_control_policy_name = "service_control_policy_name"
    puppet_account_id = "puppet_account_id"

    region = "region"
    account_id = "account_id"
    ou_name = "ou_name"

    content = {}
    description = "description"

    requested_priority = 9

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.service_control_policies import (
            do_execute_service_control_policies_task,
        )

        self.module = do_execute_service_control_policies_task

        self.sut = self.module.DoExecuteServiceControlPoliciesTask(
            manifest_file_path=self.manifest_file_path,
            service_control_policy_name=self.service_control_policy_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            account_id=self.account_id,
            requested_priority=self.requested_priority,
            ou_name=self.ou_name,
            content=self.content,
            description=self.description,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "service_control_policy_name": self.service_control_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "ou_name": self.ou_name,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"organizations.attach_policy_{self.region}",
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
