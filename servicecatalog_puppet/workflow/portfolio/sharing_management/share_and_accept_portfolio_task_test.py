from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ShareAndAcceptPortfolioForAccountTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    portfolio_task_reference = "portfolio_task_reference"
    share_tag_options = True
    share_principals = True
    describe_portfolio_shares_task_ref = "describe_portfolio_shares_task_ref"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.sharing_management import (
            share_and_accept_portfolio_task,
        )

        self.module = share_and_accept_portfolio_task

        self.sut = self.module.ShareAndAcceptPortfolioForAccountTask(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            portfolio_task_reference=self.portfolio_task_reference,
            share_tag_options=self.share_tag_options,
            share_principals=self.share_principals,
            describe_portfolio_shares_task_ref=self.describe_portfolio_shares_task_ref,
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
            "share_tag_options": self.share_tag_options,
            "share_principals": self.share_principals,
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
