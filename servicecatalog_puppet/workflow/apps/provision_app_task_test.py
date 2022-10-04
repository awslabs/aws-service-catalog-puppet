from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ProvisionAppTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    app_name = "app_name"
    region = "region"
    account_id = "account_id"
    bucket = "bucket"
    key = "key"
    version_id = "version_id"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    ssm_param_outputs = []
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.apps import provision_app_task

        self.module = provision_app_task

        self.sut = self.module.ProvisionAppTask(
            **self.get_common_args(),
            app_name=self.app_name,
            region=self.region,
            account_id=self.account_id,
            bucket=self.bucket,
            key=self.key,
            version_id=self.version_id,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            ssm_param_outputs=self.ssm_param_outputs,
            execution=self.execution
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "app_name": self.app_name,
            "region": self.region,
            "account_id": self.account_id,
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
        self.assert_empty_output()
