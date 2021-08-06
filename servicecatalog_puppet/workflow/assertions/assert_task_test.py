#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip, mock

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class AssertTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    assertion_name = "assertion_name"
    region = "region"
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    expected = {}
    actual = {}
    execution = constants.EXECUTION_MODE_HUB
    requested_priority = 1

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.assertions import assert_task

        self.module = assert_task

        self.sut = self.module.AssertTask(
            manifest_file_path=self.manifest_file_path,
            assertion_name=self.assertion_name,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
            expected=self.expected,
            actual=self.actual,
            requested_priority=self.requested_priority,
            execution=self.execution,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "region": self.region,
            "account_id": self.account_id,
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

    @mock.patch(
        "servicecatalog_puppet.workflow.dependency.DependenciesMixin.get_section_dependencies"
    )
    def test_requires(
        self, get_section_dependencies_mock,
    ):
        # setup
        get_section_dependencies_mock.return_value = ["a"]
        requirements = {"section_dependencies": self.sut.get_section_dependencies()}

        expected_result = requirements

        # exercise
        actual_result = self.sut.requires()

        # assert
        self.assertEqual(expected_result, actual_result)
