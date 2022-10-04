from unittest import skip, mock
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoExecuteCodeBuildRunTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    code_build_run_name = "code_build_run_name"
    region = "region"
    account_id = "account_id"
    project_name = "project_name"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.codebuild_runs import (
            do_execute_code_build_run_task,
        )

        self.module = do_execute_code_build_run_task

        self.sut = self.module.DoExecuteCodeBuildRunTask(
            **self.get_common_args(),
            code_build_run_name=self.code_build_run_name,
            region=self.region,
            account_id=self.account_id,
            project_name=self.project_name,
            manifest_file_path=self.manifest_file_path,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "code_build_run_name": self.code_build_run_name,
            "region": self.region,
            "account_id": self.account_id,
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
