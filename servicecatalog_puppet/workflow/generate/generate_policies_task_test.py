#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os

from servicecatalog_puppet import constants
from servicecatalog_puppet import environmental_variables
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GeneratePoliciesTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    region = "region"
    account_id = "account_id"
    organizations_to_share_with = dict(a=1)
    ous_to_share_with = dict(b=2)
    accounts_to_share_with = dict(c=3)

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.generate import generate_policies_task

        self.module = generate_policies_task

        self.sut = self.module.GeneratePolicies(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            organizations_to_share_with=self.organizations_to_share_with,
            ous_to_share_with=self.ous_to_share_with,
            accounts_to_share_with=self.accounts_to_share_with,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)
