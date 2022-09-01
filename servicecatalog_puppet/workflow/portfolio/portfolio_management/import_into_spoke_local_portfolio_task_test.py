from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ImportIntoSpokeLocalPortfolioTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    portfolio_task_reference = "portfolio_task_reference"
    hub_portfolio_task_reference = "hub_portfolio_task_reference"
    portfolio_get_all_products_and_their_versions_ref = (
        "portfolio_get_all_products_and_their_versions_ref"
    )
    portfolio_get_all_products_and_their_versions_for_hub_ref = (
        "portfolio_get_all_products_and_their_versions_for_hub_ref"
    )

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
            import_into_spoke_local_portfolio_task,
        )

        self.module = import_into_spoke_local_portfolio_task

        self.sut = self.module.ImportIntoSpokeLocalPortfolioTask(
            **self.get_common_args(),
            account_id=self.account_id,
            region=self.region,
            portfolio_task_reference=self.portfolio_task_reference,
            hub_portfolio_task_reference=self.hub_portfolio_task_reference,
            portfolio_get_all_products_and_their_versions_ref=self.portfolio_get_all_products_and_their_versions_ref,
            portfolio_get_all_products_and_their_versions_for_hub_ref=self.portfolio_get_all_products_and_their_versions_for_hub_ref,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.search_products_as_admin_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioning_artifacts_{self.account_id}_{self.region}",
            f"servicecatalog.associate_product_with_portfolio_{self.account_id}_{self.region}",
        ]

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