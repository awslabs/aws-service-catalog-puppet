from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class AssertionForRegionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    assertion_name = "assertion_name"
    puppet_account_id = "puppet_account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.assertions import assertion_for_region_task

        self.module = assertion_for_region_task

        self.sut = self.module.AssertionForRegionTask(
            puppet_account_id=self.puppet_account_id,
            assertion_name=self.assertion_name,
            manifest_file_path=self.manifest_file_path,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    