from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class CodeBuildRunBaseTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.codebuild_runs import (
            code_build_run_base_task,
        )

        self.module = code_build_run_base_task

        self.sut = self.module.CodeBuildRunBaseTask(
            manifest_file_path=self.manifest_file_path
        )

        self.wire_up_mocks()
