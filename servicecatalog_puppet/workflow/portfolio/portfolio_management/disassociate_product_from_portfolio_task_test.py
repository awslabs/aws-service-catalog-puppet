#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DisassociateProductFromPortfolioTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    account_id = "account_id"
    region = "region"
    portfolio_id = "portfolio_id"
    product_id = "product_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            disassociate_product_from_portfolio_task,
        )

        self.module = disassociate_product_from_portfolio_task

        self.sut = self.module.DisassociateProductFromPortfolio(
            manifest_file_path=self.manifest_file_path,
            account_id=self.account_id,
            region=self.region,
            portfolio_id=self.portfolio_id,
            product_id=self.product_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio_id": self.portfolio_id,
            "product_id": self.product_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"servicecatalog.disassociate_product_from_portfolio_{self.account_id}_{self.region}_{self.portfolio_id}_{self.product_id}": 1,
        }

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        result = dict(foo="bar")
        self.inject_spoke_regional_client_called_with_response(
            "servicecatalog", "disassociate_product_from_portfolio", result
        )

        # exercise
        self.sut.run()

        # verify
        self.assert_spoke_regional_client_called_with(
            "servicecatalog",
            "disassociate_product_from_portfolio",
            dict(PortfolioId=self.portfolio_id, ProductId=self.product_id,),
        )
        self.assert_output(result)
