from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class TerminateResourceUpdateConstraintsForSpokeLocalPortfolioTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.constraints_management import (
            terminate_resource_update_constraints_for_spoke_local_portfolio_task,
        )

        self.module = (
            terminate_resource_update_constraints_for_spoke_local_portfolio_task
        )

        self.sut = self.module.TerminateResourceUpdateConstraintsForSpokeLocalPortfolioTask(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
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
