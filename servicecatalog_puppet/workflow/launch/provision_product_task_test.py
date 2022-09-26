from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ProvisionProductTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    region = "region"
    account_id = "account_id"
    portfolio = "portfolio"
    product = "product"
    version = "version"
    portfolio_get_all_products_and_their_versions_ref = (
        "portfolio_get_all_products_and_their_versions_ref"
    )
    describe_provisioning_params_ref = "describe_provisioning_params_ref"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    ssm_param_outputs = []
    tags = []
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import provision_product_task

        self.module = provision_product_task

        self.sut = self.module.ProvisionProductTask(
            **self.get_common_args(),
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            region=self.region,
            account_id=self.account_id,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            portfolio_get_all_products_and_their_versions_ref=self.portfolio_get_all_products_and_their_versions_ref,
            describe_provisioning_params_ref=self.describe_provisioning_params_ref,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            ssm_param_outputs=self.ssm_param_outputs,
            execution=self.execution,
            tags=self.tags,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
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
