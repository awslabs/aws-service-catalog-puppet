from unittest import skip
from . import tasks_unit_tests_helper


class SpokeLocalPortfolioSectionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    execution_mode = "execution_mode"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import spoke_local_portfolios

        self.module = spoke_local_portfolios

        self.sut = self.module.SpokeLocalPortfolioSectionTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            include_expanded_from=self.include_expanded_from,
            single_account=self.single_account,
            is_dry_run=self.is_dry_run,
            execution_mode=self.execution_mode,
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_requires(self):
        # setup
        # exercise
        actual_result = self.sut.requires()

        # verify
        raise NotImplementedError()

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
