#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class SSMOutputsTasksTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    param_name = "param_name"
    stack_output = "stack_output"
    task_generating_output = "task_generating_output"
    task_generating_output_account_id = "task_generating_output_account_id"
    task_generating_output_region = "task_generating_output_region"
    task_generating_output_section_name = "task_generating_output_section_name"
    task_generating_output_entity_name = "task_generating_output_entity_name"
    task_generating_output_stack_set_name = "task_generating_output_stack_set_name"
    task_generating_output_launch_name = "task_generating_output_launch_name"
    force_operation = False

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.ssm import ssm_outputs_task

        self.module = ssm_outputs_task

        self.sut = self.module.SSMOutputsTasks(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            param_name=self.param_name,
            stack_output=self.stack_output,
            task_generating_output=self.task_generating_output,
            task_generating_output_account_id=self.task_generating_output_account_id,
            task_generating_output_region=self.task_generating_output_region,
            task_generating_output_section_name=self.task_generating_output_section_name,
            task_generating_output_entity_name=self.task_generating_output_entity_name,
            task_generating_output_stack_set_name=self.task_generating_output_stack_set_name,
            task_generating_output_launch_name=self.task_generating_output_launch_name,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
            "stack_output": self.stack_output,
            "force_operation": self.force_operation,
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


class TerminateSSMOutputsTasksTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    account_id = "account_id"
    region = "region"
    param_name = "param_name"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.ssm import ssm_outputs_task

        self.module = ssm_outputs_task

        self.sut = self.module.TerminateSSMOutputsTasks(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            param_name=self.param_name,
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

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
