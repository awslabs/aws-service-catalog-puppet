from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class CreateAssociationsForSpokeLocalPortfolioTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    portfolio_task_reference = "portfolio_task_reference"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    associations = []

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.associations import (
            create_associations_for_spoke_local_portfolio_task,
        )

        self.module = create_associations_for_spoke_local_portfolio_task

        self.sut = self.module.CreateAssociationsForSpokeLocalPortfolioTask(
            **self.get_common_args(),
            portfolio_task_reference=self.portfolio_task_reference,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            associations=self.associations,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
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
