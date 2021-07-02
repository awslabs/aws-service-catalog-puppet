from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LambdaInvocationForRegionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    region = "region"
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    lambda_invocation_name = "lambda_invocation_name"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            lambda_invocation_for_region_task,
        )

        self.module = lambda_invocation_for_region_task

        self.sut = self.module.LambdaInvocationForRegionTask(
            lambda_invocation_name=self.lambda_invocation_name,
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    