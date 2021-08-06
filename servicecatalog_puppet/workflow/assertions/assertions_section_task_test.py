from servicecatalog_puppet.workflow import tasks_unit_tests_helper
from unittest import skip, mock
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.assertions import (
    assertion_for_region_task,
    assertion_for_account_task,
    assertion_for_account_and_region_task,
    assertion_task,
)


class AssertionsSectionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.assertions import assertions_section_task

        self.module = assertions_section_task

        self.sut = self.module.AssertionsSectionTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
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
