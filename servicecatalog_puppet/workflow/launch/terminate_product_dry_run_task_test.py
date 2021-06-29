from servicecatalog_puppet.workflow import tasks_unit_tests_helper
from unittest import skip


class TerminateProductDryRunTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    portfolio = "portfolio"
    portfolio_id = "portfolio_id"
    product = "product"
    product_id = "product_id"
    version = "version"
    version_id = "version_id"
    account_id = "account_id"
    region = "region"
    puppet_account_id = "puppet_account_id"
    retry_count = 1
    ssm_param_outputs = []
    worker_timeout = 3
    parameters = {}
    ssm_param_inputs = []

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import terminate_product_dry_run_task

        self.module = terminate_product_dry_run_task

        self.sut = self.module.TerminateProductDryRunTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
            product=self.product,
            product_id=self.product_id,
            version=self.version,
            version_id=self.version_id,
            account_id=self.account_id,
            region=self.region,
            puppet_account_id=self.puppet_account_id,
            retry_count=self.retry_count,
            ssm_param_outputs=self.ssm_param_outputs,
            worker_timeout=self.worker_timeout,
            parameters=self.parameters,
            ssm_param_inputs=self.ssm_param_inputs,
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
        self.assertDictEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",
        ]

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
