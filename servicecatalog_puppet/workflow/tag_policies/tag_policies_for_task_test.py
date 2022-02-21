#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class TagPoliciesForTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    tag_policies_name = "tag_policies_name"
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.tag_policies import tag_policies_for_task

        self.module = tag_policies_for_task

        self.sut = self.module.TagPoliciesForTask(
            manifest_file_path=self.manifest_file_path,
            tag_policies_name=self.tag_policies_name,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "tag_policies_name": self.tag_policies_name,
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
