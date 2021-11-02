#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LambdaInvocationForAccountTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    lambda_invocation_name = "lambda_invocation_name"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            lambda_invocation_for_account_task,
        )

        self.module = lambda_invocation_for_account_task

        self.sut = self.module.LambdaInvocationForAccountTask(
            puppet_account_id=self.puppet_account_id,
            lambda_invocation_name=self.lambda_invocation_name,
            manifest_file_path=self.manifest_file_path,
            account_id=self.account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)
