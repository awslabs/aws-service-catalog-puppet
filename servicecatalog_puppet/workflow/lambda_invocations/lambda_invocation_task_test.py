from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LambdaInvocationTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    lambda_invocation_name = "lambda_invocation_name"
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            lambda_invocation_task,
        )

        self.module = lambda_invocation_task

        self.sut = self.module.LambdaInvocationTask(
            lambda_invocation_name=self.lambda_invocation_name,
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    
    def test_run(self):
        # setup
        # exercise
        self.sut.run()

        # verify
        self.assert_output(self.sut.params_for_results_display())
