from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class SharePortfolioViaOrgsTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    region = "region"
    portfolio = "portfolio"
    ou_to_share_with = "ou_to_share_with"
    portfolio_task_reference = "portfolio_task_reference"
    share_tag_options = True
    share_principals = True
    describe_portfolio_shares_task_ref = "describe_portfolio_shares_task_ref"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.sharing_management import (
            share_portfolio_via_orgs_task,
        )

        self.module = share_portfolio_via_orgs_task

        self.sut = self.module.SharePortfolioViaOrgsTask(
            **self.get_common_args(),
            region=self.region,
            portfolio=self.portfolio,
            ou_to_share_with=self.ou_to_share_with,
            portfolio_task_reference=self.portfolio_task_reference,
            share_tag_options=self.share_tag_options,
            share_principals=self.share_principals,
            describe_portfolio_shares_task_ref=self.describe_portfolio_shares_task_ref,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "ou_to_share_with": self.ou_to_share_with,
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
