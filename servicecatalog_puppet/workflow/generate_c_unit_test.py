from . import tasks_unit_tests

import pytest


class GeneratePoliciesTemplateTest(tasks_unit_tests.PuppetTaskUnitTest):
    region = "eu-west-0"
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"

    def setUp(self) -> None:
        from . import generate

        self.sut = generate.GeneratePoliciesTemplate(
            region=self.region,
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            should_use_sns=True,
            should_use_product_plans=True,
            include_expanded_from=True,
            single_account=True,
            is_dry_run=True,
            execution_mode="hub",
            sharing_policies=dict(),
        )

    def test_params_for_results_display(self):
        expected_result = {
            "region": self.region,
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class EnsureEventBridgeEventBusTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    region = "eu-west-0"
    puppet_account_id = "01234567890"

    def setUp(self) -> None:
        from . import generate

        self.sut = generate.EnsureEventBridgeEventBusTask(
            region=self.region, puppet_account_id=self.puppet_account_id,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "region": self.region,
            "puppet_account_id": self.puppet_account_id,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class GeneratePoliciesTest(tasks_unit_tests.PuppetTaskUnitTest):
    region = "eu-west-0"
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"
    sharing_policies = dict()

    should_use_sns = False
    should_use_product_plans = True
    include_expanded_from = True
    single_account = None
    is_dry_run = False
    execution_mode = "hub"

    def setUp(self) -> None:
        from . import generate

        self.sut = generate.GeneratePolicies(
            region=self.region,
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            sharing_policies=self.sharing_policies,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            include_expanded_from=self.include_expanded_from,
            single_account=self.single_account,
            is_dry_run=self.is_dry_run,
            execution_mode=self.execution_mode,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "region": self.region,
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())

    def test_requires(self):
        from . import generate

        expected_result = {
            "template": generate.GeneratePoliciesTemplate(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                region=self.region,
                should_use_sns=self.should_use_sns,
                should_use_product_plans=self.should_use_product_plans,
                include_expanded_from=self.include_expanded_from,
                single_account=self.single_account,
                is_dry_run=self.is_dry_run,
                execution_mode=self.execution_mode,
                sharing_policies=self.sharing_policies,
            ),
        }
        self.assertEqual(expected_result, self.sut.requires())


class GenerateSharesTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"

    should_use_sns = False
    should_use_product_plans = True
    include_expanded_from = True
    single_account = None
    is_dry_run = False
    execution_mode = "hub"

    def setUp(self) -> None:
        from . import generate

        self.sut = generate.GenerateSharesTask(
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
