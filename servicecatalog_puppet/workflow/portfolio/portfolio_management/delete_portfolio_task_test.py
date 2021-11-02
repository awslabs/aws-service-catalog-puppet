#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DeletePortfolioTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    product_generation_method = "product_generation_method"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            delete_portfolio_task,
        )

        self.module = delete_portfolio_task

        self.sut = self.module.DeletePortfolio(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            product_generation_method=self.product_generation_method,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        self.sut.run()
        # verify
        raise NotImplementedError()
