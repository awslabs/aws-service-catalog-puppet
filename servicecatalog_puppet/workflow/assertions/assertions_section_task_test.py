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

    @mock.patch(
        "servicecatalog_puppet.workflow.manifest.manifest_mixin.ManifestMixen.manifest"
    )
    def test_requires(self, manifest_mock):
        # setup
        requirements = list()

        for name, details in self.sut.manifest.get(constants.ASSERTIONS, {}).items():
            requirements += self.sut.handle_requirements_for(
                name,
                constants.ASSERTION,
                constants.ASSERTIONS,
                assertion_for_region_task.AssertionForRegionTask,
                assertion_for_account_task.AssertionForAccountTask,
                assertion_for_account_and_region_task.AssertionForAccountAndRegionTask,
                assertion_task.AssertionTask,
                dict(
                    assertion_name=name,
                    puppet_account_id=self.sut.puppet_account_id,
                    manifest_file_path=self.sut.manifest_file_path,
                ),
            )

        expected_result = requirements

        # exercise
        actual_result = self.sut.requires()

        # assert
        self.assertEqual(expected_result, actual_result)
