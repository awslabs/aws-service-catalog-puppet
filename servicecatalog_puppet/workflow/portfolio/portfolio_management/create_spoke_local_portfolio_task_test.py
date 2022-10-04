from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class CreateSpokeLocalPortfolioTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    portfolio_task_reference = "portfolio_task_reference"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            create_spoke_local_portfolio_task,
        )

        self.module = create_spoke_local_portfolio_task

        self.sut = self.module.CreateSpokeLocalPortfolioTask(
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
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
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
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
