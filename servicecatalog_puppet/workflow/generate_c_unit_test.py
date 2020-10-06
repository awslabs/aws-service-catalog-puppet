from . import tasks_unit_tests

import pytest


class GeneratePoliciesTemplateTest(tasks_unit_tests.PuppetTaskUnitTest):
    region = "eu-west-0"
    puppet_account_id = "01234567890"
    manifest_file_path = "tcvyuiho"
    cache_invalidator = "foo"

    def setUp(self) -> None:
        from . import generate

        self.sut = generate.GeneratePoliciesTemplate(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            region=self.region,
            sharing_policies=dict(),
            cache_invalidator=self.cache_invalidator,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
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
    cache_invalidator = "foo"

    def setUp(self) -> None:
        from . import generate

        self.sut = generate.GeneratePolicies(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            region=self.region,
            sharing_policies=self.sharing_policies,
            should_use_sns=self.should_use_sns,
            cache_invalidator=self.cache_invalidator,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "should_use_sns": self.should_use_sns,
            "cache_invalidator": self.cache_invalidator,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())

    def test_requires(self):
        from . import generate

        expected_result = {
            "template": generate.GeneratePoliciesTemplate(
                puppet_account_id=self.puppet_account_id,
                manifest_file_path=self.manifest_file_path,
                region=self.region,
                sharing_policies=dict(),
                cache_invalidator="foo",
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

    section = "launches"
    cache_invalidator = "food"

    def setUp(self) -> None:
        from . import generate

        self.sut = generate.GenerateSharesTask(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            should_use_sns=self.should_use_sns,
            section=self.section,
            cache_invalidator=self.cache_invalidator,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "section": self.section,
            "cache_invalidator": self.cache_invalidator,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())
