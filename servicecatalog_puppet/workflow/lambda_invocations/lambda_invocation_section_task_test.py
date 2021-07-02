from unittest import skip, mock

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LambdaInvocationsSectionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            lambda_invocation_section_task,
        )

        self.module = lambda_invocation_section_task

        self.sut = self.module.LambdaInvocationsSectionTask(
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

    
    def test_run(self):
        # setup
        lambda_invocations = dict(foo="bar")
        manifest = {
            "lambda-invocations": lambda_invocations,
        }
        manifest_mocked = mock.PropertyMock(return_value=manifest)
        type(self.sut).manifest = manifest_mocked

        # exercise
        self.sut.run()

        # verify
        self.assert_output(lambda_invocations)
