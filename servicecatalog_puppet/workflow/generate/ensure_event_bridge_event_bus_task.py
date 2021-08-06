#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks


class EnsureEventBridgeEventBusTask(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
        }

    def api_calls_used(self):
        return {
            f"events.describe_event_bus_{self.puppet_account_id}_{self.region}": 1,
            f"events.create_event_bus_{self.puppet_account_id}_{self.region}": 1,
        }

    def run(self):
        with self.hub_regional_client("events") as events:
            created = False
            try:
                events.describe_event_bus(Name=constants.EVENT_BUS_NAME)
                created = True
            except events.exceptions.ResourceNotFoundException:
                events.create_event_bus(Name=constants.EVENT_BUS_NAME)
        self.write_output(created)
