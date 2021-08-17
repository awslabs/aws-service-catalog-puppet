#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip, mock

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class InvokeLambdaTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    lambda_invocation_name = "lambda_invocation_name"
    region = "region"
    account_id = "account_id"
    function_name = "function_name"
    qualifier = "qualifier"
    invocation_type = "invocation_type"
    puppet_account_id = "puppet_account_id"
    execution = "spoke"
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import invoke_lambda_task

        self.module = invoke_lambda_task

        self.sut = self.module.InvokeLambdaTask(
            lambda_invocation_name=self.lambda_invocation_name,
            region=self.region,
            account_id=self.account_id,
            function_name=self.function_name,
            qualifier=self.qualifier,
            invocation_type=self.invocation_type,
            puppet_account_id=self.puppet_account_id,
            execution=self.execution,
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

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()

    @mock.patch(
        "servicecatalog_puppet.workflow.dependency.DependenciesMixin.get_section_dependencies"
    )
    def test_requires(self, get_section_dependencies_mock):
        # setup
        get_section_dependencies_mock.return_value = ["a"]
        requirements = {"section_dependencies": self.sut.get_section_dependencies()}

        expected_result = requirements

        # exercise
        actual_result = self.sut.requires()

        # assert
        self.assertEqual(expected_result, actual_result)
