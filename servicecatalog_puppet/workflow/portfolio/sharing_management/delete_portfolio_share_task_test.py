#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DeletePortfolioShareTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.sharing_management import (
            delete_portfolio_share_task,
        )

        self.module = delete_portfolio_share_task

        self.sut = self.module.DeletePortfolioShare(
            manifest_file_path=self.manifest_file_path,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
            f"servicecatalog.delete_portfolio_share_{self.puppet_account_id}_{self.region}_{self.portfolio}",
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
