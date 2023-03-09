#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import unittest

from servicecatalog_puppet.waluigi.constants import RESOURCES_REQUIRED


class TestExternal(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        from servicecatalog_puppet.waluigi.locks import external

        self.sut = external

    def test_are_resources_are_free_for_task_dict_with_no_locked_resources(self):
        # setup
        resources_in_use = dict()
        task_parameters = dict()
        task_parameters[RESOURCES_REQUIRED] = ["aaaa"]
        expected_result = True

        # exercise
        actual_result, _ = self.sut.are_resources_are_free_for_task_dict(
            task_parameters, resources_in_use
        )

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_are_resources_are_free_for_task_dict_with_other_locked_resources(self):
        # setup
        resources_in_use = dict(bbbb="some-other-task")
        task_parameters = dict()
        task_parameters[RESOURCES_REQUIRED] = ["aaaa"]
        expected_result = True

        # exercise
        actual_result, _ = self.sut.are_resources_are_free_for_task_dict(
            task_parameters, resources_in_use
        )

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_are_resources_are_free_for_task_dict_with_locked_resources(self):
        # setup
        resources_in_use = dict(aaaa="some-other-task")
        task_parameters = dict()
        task_parameters[RESOURCES_REQUIRED] = ["aaaa"]
        expected_result = False

        # exercise
        actual_result, _ = self.sut.are_resources_are_free_for_task_dict(
            task_parameters, resources_in_use
        )

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_are_resources_are_free_for_task_dict_with_locked_resources_and_more(self):
        # setup
        resources_in_use = dict(aaaa="some-other-task", bbb="sdsnkdnsk")
        task_parameters = dict()
        task_parameters[RESOURCES_REQUIRED] = ["aaaa"]
        expected_result = False

        # exercise
        actual_result, _ = self.sut.are_resources_are_free_for_task_dict(
            task_parameters, resources_in_use
        )

        # verify
        self.assertEqual(expected_result, actual_result)
