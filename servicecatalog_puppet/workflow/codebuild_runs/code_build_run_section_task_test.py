from unittest import skip, mock
from servicecatalog_puppet.workflow import tasks_unit_tests_helper
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.codebuild_runs import (
    code_build_run_for_region_task,
    code_build_run_for_account_task,
    code_build_run_for_account_and_region_task,
    code_build_run_task,
)


class CodeBuildRunsSectionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    cache_invalidator = "NOW"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.codebuild_runs import (
            code_build_run_section_task,
        )

        self.module = code_build_run_section_task

        self.sut = self.module.CodeBuildRunsSectionTask(
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

        for name, details in self.sut.manifest.get(
            constants.CODE_BUILD_RUNS, {}
        ).items():
            requirements += self.sut.handle_requirements_for(
                name,
                constants.CODE_BUILD_RUN,
                constants.CODE_BUILD_RUNS,
                code_build_run_for_region_task.CodeBuildRunForRegionTask,
                code_build_run_for_account_task.CodeBuildRunForAccountTask,
                code_build_run_for_account_and_region_task.CodeBuildRunForAccountAndRegionTask,
                code_build_run_task.CodeBuildRunTask,
                dict(
                    code_build_run_name=name,
                    puppet_account_id=self.sut.puppet_account_id,
                    manifest_file_path=self.sut.manifest_file_path,
                ),
            )

        expected_result = requirements

        # exercise
        actual_result = self.sut.requires()

        # assert
        self.assertEqual(expected_result, actual_result)
