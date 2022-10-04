from unittest import skip, mock
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GetPortfolioLocalTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    status = "status"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            get_portfolio_task,
        )

        self.module = get_portfolio_task

        self.sut = self.module.GetPortfolioLocalTask(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            status=self.status,
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

    def test_run(self):
        # setup
        self.sut.get_portfolio_details = mock.MagicMock(name="get_portfolio_details")

        # exercise
        self.sut.run()

        # verify
        self.assert_output(self.sut.get_portfolio_details())


class GetPortfolioImportedTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    sharing_mode = "sharing_mode"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            get_portfolio_task,
        )

        self.module = get_portfolio_task

        self.sut = self.module.GetPortfolioImportedTask(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            sharing_mode=self.sharing_mode,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "sharing_mode": self.sharing_mode,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        self.sut.get_portfolio_details = mock.MagicMock(name="get_portfolio_details")

        # exercise
        self.sut.run()

        # verify
        self.assert_output(self.sut.get_portfolio_details())
