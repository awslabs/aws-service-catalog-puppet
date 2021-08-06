#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DisassociateProductsFromPortfolioTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    account_id = "account_id"
    region = "region"
    portfolio_id = "portfolio_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            disassociate_products_from_portfolio_task,
        )

        self.module = disassociate_products_from_portfolio_task

        self.sut = self.module.DisassociateProductsFromPortfolio(
            manifest_file_path=self.manifest_file_path,
            account_id=self.account_id,
            region=self.region,
            portfolio_id=self.portfolio_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio_id": self.portfolio_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"servicecatalog.search_products_as_admin_single_page_{self.account_id}_{self.region}_{self.portfolio_id}": 1,
        }

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        # exercise
        self.sut.run()

        # verify
        self.assert_output(self.sut.params_for_results_display())
