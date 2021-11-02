#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class RequestPolicyTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    type = "type"
    region = "region"
    account_id = "account_id"
    organization = "organization"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.sharing_management import (
            request_policy_task,
        )

        self.module = request_policy_task

        self.sut = self.module.RequestPolicyTask(
            manifest_file_path=self.manifest_file_path,
            type=self.type,
            region=self.region,
            account_id=self.account_id,
            organization=self.organization,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "type": self.type,
            "account_id": self.account_id,
            "region": self.region,
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
