from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ProvisionStackTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    stack_name = "stack_name"
    region = "region"
    account_id = "account_id"
    bucket = "bucket"
    key = "key"
    version_id = "version_id"
    launch_name = "launch_name"
    stack_set_name = "stack_set_name"
    get_s3_template_ref = "get_s3_template_ref"
    capabilities = []
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    ssm_param_outputs = []
    execution = "execution"
    manifest_file_path = "manifest_file_path"
    tags = []

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.stack import provision_stack_task

        self.module = provision_stack_task

        self.sut = self.module.ProvisionStackTask(
            **self.get_common_args(),
            stack_name=self.stack_name,
            region=self.region,
            account_id=self.account_id,
            bucket=self.bucket,
            key=self.key,
            version_id=self.version_id,
            launch_name=self.launch_name,
            stack_set_name=self.stack_set_name,
            get_s3_template_ref=self.get_s3_template_ref,
            capabilities=self.capabilities,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            ssm_param_outputs=self.ssm_param_outputs,
            execution=self.execution,
            manifest_file_path=self.manifest_file_path,
            tags=self.tags,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "stack_name": self.stack_name,
            "account_id": self.account_id,
            "region": self.region,
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
