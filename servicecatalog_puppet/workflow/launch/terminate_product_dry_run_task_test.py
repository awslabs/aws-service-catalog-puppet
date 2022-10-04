from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class TerminateProductDryRunTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    launch_name = "launch_name"
    region = "region"
    account_id = "account_id"
    portfolio = "portfolio"
    product = "product"
    version = "version"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    ssm_param_outputs = []
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import terminate_product_dry_run_task

        self.module = terminate_product_dry_run_task

        self.sut = self.module.TerminateProductDryRunTask(
            **self.get_common_args(),
            launch_name=self.launch_name,
            region=self.region,
            account_id=self.account_id,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            ssm_param_outputs=self.ssm_param_outputs,
            execution=self.execution,
        )

        self.wire_up_mocks()

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
