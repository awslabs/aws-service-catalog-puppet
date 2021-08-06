#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DeleteCloudFormationStackTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    stack_name = "stack_name"
    nonce = "nonce"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.general import (
            delete_cloud_formation_stack_task,
        )

        self.module = delete_cloud_formation_stack_task

        self.sut = self.module.DeleteCloudFormationStackTask(
            account_id=self.account_id,
            region=self.region,
            stack_name=self.stack_name,
            nonce=self.nonce,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "stack_name": self.stack_name,
            "account_id": self.account_id,
            "region": self.region,
            "nonce": self.nonce,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"cloudformation.describe_stacks_single_page_{self.account_id}_{self.region}": 1,
            f"cloudformation.delete_stack_{self.account_id}_{self.region}": 1,
            f"cloudformation.describe_stack_events_{self.account_id}_{self.region}": 1,
        }

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        # exercise
        self.sut.run()
        # verify
        self.assert_spoke_regional_client_called_with(
            "cloudformation", "ensure_deleted", dict(StackName=self.stack_name)
        )
        self.assert_output(self.sut.params_for_results_display())
