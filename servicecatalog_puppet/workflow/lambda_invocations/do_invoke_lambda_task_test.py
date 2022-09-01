from unittest import skip, mock
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoInvokeLambdaTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    lambda_invocation_name = "lambda_invocation_name"
    region = "region"
    account_id = "account_id"
    function_name = "function_name"
    qualifier = "qualifier"
    invocation_type = "invocation_type"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            do_invoke_lambda_task,
        )

        self.module = do_invoke_lambda_task

        self.sut = self.module.DoInvokeLambdaTask(
            **self.get_common_args(),
            lambda_invocation_name=self.lambda_invocation_name,
            region=self.region,
            account_id=self.account_id,
            function_name=self.function_name,
            qualifier=self.qualifier,
            invocation_type=self.invocation_type,
            manifest_file_path=self.manifest_file_path,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        self.sut.get_account_used = mock.MagicMock(name="get_account_used")
        expected_result = {
            f"lambda.invoke_{self.sut.get_account_used()}_{self.region}": 1,
        }

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
