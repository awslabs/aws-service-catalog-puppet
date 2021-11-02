#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class CodeBuildRunForTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    code_build_run_name = "code_build_run_name"
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.codebuild_runs import (
            code_build_run_for_task,
        )

        self.module = code_build_run_for_task

        self.sut = self.module.CodeBuildRunForTask(
            manifest_file_path=self.manifest_file_path,
            code_build_run_name=self.code_build_run_name,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "code_build_run_name": self.code_build_run_name,
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
