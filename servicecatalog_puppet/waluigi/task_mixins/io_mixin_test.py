#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import unittest

from servicecatalog_puppet import constants


class IOMixinTest(unittest.TestCase):
    def setUp(self) -> None:
        from servicecatalog_puppet.waluigi.task_mixins import io_mixin

        self.module = io_mixin
        self.sut = self.module.IOMixin()

    def test_should_use_s3_target_if_caching_is_on(self):
        # setup
        self.sut.cachable_level = constants.CACHE_LEVEL_NO_CACHE
        expected_result = False

        # execute
        actual_result = self.sut.should_use_s3_target_if_caching_is_on

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_should_use_s3_target_if_caching_is_on_when_off(self):
        # setup
        caching_enabled = [
            constants.CACHE_LEVEL_RUN,
            constants.CACHE_LEVEL_PERMANENT,
            constants.CACHE_LEVEL_TASK,
            constants.CACHE_LEVEL_DEFAULT,
        ]
        expected_result = True

        # execute
        for result in caching_enabled:
            self.sut.cachable_level = result
            # verify
            self.assertEqual(
                expected_result, self.sut.should_use_s3_target_if_caching_is_on, result
            )
