#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ServiceControlPoliciesForAccountAndRegionTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    account_id = "account_id"
    region = "region"
    puppet_account_id = "puppet_account_id"
    service_control_policies_name = "service_control_policies_name"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.service_control_policies import (
            service_control_policies_for_account_and_region_task,
        )

        self.module = service_control_policies_for_account_and_region_task

        self.sut = self.module.ServiceControlPoliciesForAccountAndRegionTask(
            manifest_file_path=self.manifest_file_path,
            service_control_policies_name=self.service_control_policies_name,
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "service_control_policies_name": self.service_control_policies_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)
