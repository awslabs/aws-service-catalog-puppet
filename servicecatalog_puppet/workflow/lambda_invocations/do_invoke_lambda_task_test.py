#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from unittest import mock

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoInvokeLambdaTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    lambda_invocation_name = "lambda_invocation_name"
    region = "region"
    account_id = "account_id"
    function_name = "function_name"
    qualifier = "qualifier"
    invocation_type = "RequestResponse"
    puppet_account_id = "puppet_account_id"
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            do_invoke_lambda_task,
        )

        self.module = do_invoke_lambda_task

        self.sut = self.module.DoInvokeLambdaTask(
            lambda_invocation_name=self.lambda_invocation_name,
            region=self.region,
            account_id=self.account_id,
            function_name=self.function_name,
            qualifier=self.qualifier,
            invocation_type=self.invocation_type,
            puppet_account_id=self.puppet_account_id,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            manifest_file_path=self.manifest_file_path,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @mock.patch("servicecatalog_puppet.config.get_home_region")
    def test_run(self, get_home_region_mock):
        # setup
        get_home_region_mock.return_value = "eu-west-0"
        self.sut.all_params = dict()
        payload = dict(
            account_id=self.account_id,
            region=self.region,
            parameters=self.sut.get_parameter_values(),
        )
        response = dict(StatusCode=200)
        self.inject_hub_regional_client_called_with_response(
            "lambda", "invoke", response,
        )

        # exercise
        self.sut.run()

        # verify
        self.assert_hub_regional_client_called_with(
            "lambda",
            "invoke",
            dict(
                FunctionName=self.function_name,
                InvocationType=self.invocation_type,
                Payload=json.dumps(payload),
                Qualifier=self.qualifier,
            ),
            dict(region_name="eu-west-0"),
        )
        self.assert_output(
            dict(
                **self.sut.params_for_results_display(),
                payload=payload,
                response=response,
            )
        )
