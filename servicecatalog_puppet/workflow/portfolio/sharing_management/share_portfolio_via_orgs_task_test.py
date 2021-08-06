#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class SharePortfolioViaOrgsTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    region = "region"
    portfolio = "portfolio"
    puppet_account_id = "puppet_account_id"
    ou_to_share_with = "ou_to_share_with"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.sharing_management import (
            share_portfolio_via_orgs_task,
        )

        self.module = share_portfolio_via_orgs_task

        self.sut = self.module.SharePortfolioViaOrgsTask(
            manifest_file_path=self.manifest_file_path,
            region=self.region,
            portfolio=self.portfolio,
            puppet_account_id=self.puppet_account_id,
            ou_to_share_with=self.ou_to_share_with,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "ou_to_share_with": self.ou_to_share_with,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.create_portfolio_share",
            f"servicecatalog.describe_portfolio_share_status",
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
