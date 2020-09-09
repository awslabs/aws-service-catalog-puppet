from . import tasks_unit_tests


class LaunchSectionTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"

    should_use_sns = False
    should_use_product_plans = True
    include_expanded_from = True
    single_account = None
    is_dry_run = False
    execution_mode = "hub"

    def setUp(self) -> None:
        from . import launch

        self.sut = launch.LaunchSectionTask(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            include_expanded_from=self.include_expanded_from,
            single_account=self.single_account,
            is_dry_run=self.is_dry_run,
            execution_mode=self.execution_mode,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())
