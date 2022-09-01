from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GetSSMParameterTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    param_name = "param_name"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.ssm import get_ssm_parameter_task

        self.module = get_ssm_parameter_task

        self.sut = self.module.GetSSMParameterTask(
            **self.get_common_args(),
            account_id=self.account_id,
            param_name=self.param_name,
            region=self.region
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
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


class GetSSMParameterByPathTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    path = "path"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.ssm import get_ssm_parameter_task

        self.module = get_ssm_parameter_task

        self.sut = self.module.GetSSMParameterByPathTask(
            **self.get_common_args(),
            account_id=self.account_id,
            path=self.path,
            region=self.region
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "path": self.path,
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
