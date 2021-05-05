from unittest import skip

from . import tasks_unit_tests_helper


class SpokeLocalPortfolioSectionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import spoke_local_portfolios

        self.module = spoke_local_portfolios

        self.sut = self.module.SpokeLocalPortfolioSectionTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
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


class SpokeLocalPortfolioTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False

    sharing_mode = "sharing_mode"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import spoke_local_portfolios

        self.module = spoke_local_portfolios

        self.sut = spoke_local_portfolios.SpokeLocalPortfolioTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
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
