#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ShareAndAcceptPortfolioTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    puppet_account_id = "puppet_account_id"
    sharing_mode = "sharing_mode"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.sharing_management import (
            share_and_accept_portfolio_task,
        )

        self.module = share_and_accept_portfolio_task

        self.sut = self.module.ShareAndAcceptPortfolioTask(
            manifest_file_path=self.manifest_file_path,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            puppet_account_id=self.puppet_account_id,
            sharing_mode=self.sharing_mode,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
            f"servicecatalog.accept_portfolio_share{self.account_id}_{self.region}",
            f"servicecatalog.associate_principal_with_portfolio{self.account_id}_{self.region}",
            f"servicecatalog.list_principals_for_portfolio{self.account_id}_{self.region}",
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
