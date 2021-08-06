#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LaunchForAccountAndRegionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    puppet_account_id = "puppet_account_id"
    launch_name = "launch_name"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import (
            launch_for_account_and_region_task,
        )

        self.module = launch_for_account_and_region_task

        self.sut = self.module.LaunchForAccountAndRegionTask(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            account_id=self.account_id,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)
