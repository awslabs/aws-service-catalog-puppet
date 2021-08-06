#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ResetProvisionedProductOwnerTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    account_id = "account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import (
            reset_provisioned_product_owner_task,
        )

        self.module = reset_provisioned_product_owner_task

        self.sut = self.module.ResetProvisionedProductOwnerTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            account_id=self.account_id,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertDictEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_properties_{self.account_id}_{self.region}",
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
