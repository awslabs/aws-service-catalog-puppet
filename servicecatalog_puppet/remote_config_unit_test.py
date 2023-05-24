#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import unittest
from unittest import mock

from servicecatalog_puppet import constants


class TestUsersOfGetConfig(unittest.TestCase):
    puppet_account_id = "abcd"
    default_region = "eu-west-0"

    def setUp(self) -> None:
        from servicecatalog_puppet import remote_config

        self.module = remote_config

    def test_get_should_simple_values(self):
        # setup
        expected_result = "banananana"
        checks_to_perform = [
            (
                self.module.get_should_use_sns,
                constants.CONFIG_SHOULD_COLLECT_CLOUDFORMATION_EVENTS,
            ),
            (
                self.module.get_should_delete_rollback_complete_stacks,
                constants.CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS,
            ),
            (self.module.get_should_use_product_plans, "should_use_product_plans"),
            (
                self.module.get_should_use_eventbridge,
                "should_forward_events_to_eventbridge",
            ),
            (
                self.module.get_should_forward_failures_to_opscenter,
                "should_forward_failures_to_opscenter",
            ),
            (self.module.get_drift_token, "drift_token"),
            (self.module.get_regions, constants.CONFIG_REGIONS),
            (self.module.is_caching_enabled, "is_caching_enabled"),
            (
                self.module.get_global_sharing_mode_default,
                "global_sharing_mode_default",
            ),
            (
                self.module.get_global_share_tag_options_default,
                "global_share_tag_options_default",
            ),
            (
                self.module.get_global_share_principals_default,
                "global_share_principals_default",
            ),
            (
                self.module.get_spoke_deploy_environment_compute_type,
                "spoke_deploy_environment_compute_type",
            ),
            (
                self.module.get_scheduler_threads_or_processes,
                "scheduler_threads_or_processes",
            ),
            (self.module.get_scheduler_algorithm, "scheduler_algorithm"),
        ]
        with mock.patch(
            "servicecatalog_puppet.remote_config.get_config"
        ) as mocked_get_config:
            for method_to_check, config_key_value in checks_to_perform:
                with self.subTest(
                    method_to_check=method_to_check, config_key_value=config_key_value
                ):
                    mocked_get_config.return_value = {config_key_value: expected_result}
                    # exercise
                    actual_result = method_to_check(
                        self.puppet_account_id, self.default_region
                    )
                    # verify
                    self.assertEquals(expected_result, actual_result)
