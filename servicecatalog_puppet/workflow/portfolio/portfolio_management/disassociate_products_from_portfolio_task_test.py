from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DisassociateProductsFromPortfolioTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    portfolio_task_reference = "portfolio_task_reference"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            disassociate_products_from_portfolio_task,
        )

        self.module = disassociate_products_from_portfolio_task

        self.sut = self.module.DisassociateProductsFromPortfolio(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            portfolio_task_reference=self.portfolio_task_reference,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
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
        expected_result = {
            f"servicecatalog.disassociate_product_from_portfolio_{self.account_id}_{self.region}": 1,
        }

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
