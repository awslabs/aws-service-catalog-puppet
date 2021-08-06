#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class EnsureEventBridgeEventBusTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.generate import (
            ensure_event_bridge_event_bus_task,
        )

        self.module = ensure_event_bridge_event_bus_task

        self.sut = self.module.EnsureEventBridgeEventBusTask(
            puppet_account_id=self.puppet_account_id, region=self.region
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"events.describe_event_bus_{self.puppet_account_id}_{self.region}": 1,
            f"events.create_event_bus_{self.puppet_account_id}_{self.region}": 1,
        }

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        from servicecatalog_puppet import constants

        # exercise
        self.sut.run()

        # verify
        self.assert_hub_regional_client_called_with(
            "events", "describe_event_bus", dict(Name=constants.EVENT_BUS_NAME)
        )
        self.assert_output(True)
