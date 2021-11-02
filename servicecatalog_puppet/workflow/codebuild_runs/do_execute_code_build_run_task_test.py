#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoExecuteCodeBuildRunTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    code_build_run_name = "code_build_run_name"
    puppet_account_id = "puppet_account_id"
    region = "region"
    account_id = "account_id"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    project_name = "project_name"
    execution = constants.EXECUTION_MODE_HUB
    requested_priority = 1

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.codebuild_runs import (
            do_execute_code_build_run_task,
        )

        self.module = do_execute_code_build_run_task

        self.sut = self.module.DoExecuteCodeBuildRunTask(
            manifest_file_path=self.manifest_file_path,
            code_build_run_name=self.code_build_run_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            account_id=self.account_id,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            project_name=self.project_name,
            requested_priority=self.requested_priority,
            execution=self.execution,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "code_build_run_name": self.code_build_run_name,
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
            f"codebuild.start_build_{self.puppet_account_id}_{self.project_name}",
            f"codebuild.batch_get_projects_{self.puppet_account_id}_{self.project_name}",
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
