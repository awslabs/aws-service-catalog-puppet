#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LaunchForTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import launch_for_task

        self.module = launch_for_task

        self.sut = self.module.LaunchForTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
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
