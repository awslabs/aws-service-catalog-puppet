#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GetSSMParameterTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    param_name = "param_name"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.ssm import get_ssm_parameter_task

        self.module = get_ssm_parameter_task

        self.sut = self.module.GetSSMParameterTask(
            **self.get_common_args(),
            account_id=self.account_id,
            param_name=self.param_name,
            region=self.region
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        parameter = dict(this="that",)
        expected_output = {self.param_name: parameter}
        self.add_expected_request_and_response(
            tasks_unit_tests_helper.SPOKE_REGIONAL_CLIENT,
            "ssm",
            "get_parameter",
            dict(Name=self.sut.get_parameter_name_to_use()),
            dict(Parameter=parameter),
        )

        # exercise
        self.sut.run()

        # verify
        self.assert_output(expected_output)


class GetSSMParameterByPathTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    path = "path"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.ssm import get_ssm_parameter_task

        self.module = get_ssm_parameter_task

        self.sut = self.module.GetSSMParameterByPathTask(
            **self.get_common_args(),
            account_id=self.account_id,
            path=self.path,
            region=self.region
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "path": self.path,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        parameter = dict(Name="that", Value="hello")
        expected_output = dict(that=parameter)
        self.add_expected_paginated_request_and_response(
            tasks_unit_tests_helper.SPOKE_REGIONAL_CLIENT,
            "ssm",
            "get_parameters_by_path",
            dict(Path=self.sut.get_parameter_path_to_use(), Recursive=True),
            [dict(Parameters=[parameter]),],
        )

        # exercise
        self.sut.run()

        # verify
        self.assert_output(expected_output)
