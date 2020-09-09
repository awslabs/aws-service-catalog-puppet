from . import tasks_unit_tests


class ManifestTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "fddsfd"
    puppet_account_id = "23094983645"

    def setUp(self) -> None:
        from . import manifest

        self.sut = manifest.ManifestTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class SectionTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "fddfdsf"
    puppet_account_id = "02345678901"
    should_use_sns = False
    should_use_product_plans = True
    include_expanded_from = True
    single_account = None
    is_dry_run = False
    execution_mode = "hub"

    def setUp(self) -> None:
        from . import manifest

        self.sut = manifest.SectionTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
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

    def test_requires(self):
        from . import manifest

        expected_result = {
            "manifest": manifest.ManifestTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
            ),
        }
        self.assertEqual(expected_result, self.sut.requires())
