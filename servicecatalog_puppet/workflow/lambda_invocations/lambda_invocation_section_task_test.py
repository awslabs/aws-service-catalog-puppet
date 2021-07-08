from unittest import skip, mock

from servicecatalog_puppet.workflow import tasks_unit_tests_helper
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_for_region_task,
    lambda_invocation_for_account_task,
    lambda_invocation_for_account_and_region_task,
    lambda_invocation_task,
)


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

    @mock.patch(
        "servicecatalog_puppet.workflow.manifest.manifest_mixin.ManifestMixen.manifest"
    )
    def test_requires(self, manifest_mock):
        # setup
        requirements = list()

        for name, details in self.sut.manifest.get(
            constants.LAMBDA_INVOCATIONS, {}
        ).items():
            requirements += self.sut.handle_requirements_for(
                name,
                constants.LAMBDA_INVOCATION,
                constants.LAMBDA_INVOCATIONS,
                lambda_invocation_for_region_task.LambdaInvocationForRegionTask,
                lambda_invocation_for_account_task.LambdaInvocationForAccountTask,
                lambda_invocation_for_account_and_region_task.LambdaInvocationForAccountAndRegionTask,
                lambda_invocation_task.LambdaInvocationTask,
                dict(
                    lambda_invocation_name=name,
                    puppet_account_id=self.sut.puppet_account_id,
                    manifest_file_path=self.sut.manifest_file_path,
                ),
            )

        expected_result = requirements

        # exercise
        actual_result = self.sut.requires()

        # assert
        self.assertEqual(expected_result, actual_result)
