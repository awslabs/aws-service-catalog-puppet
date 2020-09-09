from . import tasks_unit_tests


class ProvisioningArtifactParametersTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "lnklknkl"
    puppet_account_id = "01234567890"
    portfolio = "port1"
    product = "prod1"
    version = "v1"
    account_id = "00987654321"
    region = "eu-west-0"

    def setUp(self) -> None:
        from . import provisioning

        self.sut = provisioning.ProvisioningArtifactParametersTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            account_id=self.account_id,
            region=self.region,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
            "account_id": self.account_id,
            "region": self.region,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())

    def test_requires(self):
        from . import portfoliomanagement as portfoliomanagement_tasks

        expected_result = {
            "details": portfoliomanagement_tasks.GetVersionIdByVersionName(
                self.puppet_account_id,
                self.manifest_file_path,
                self.portfolio,
                self.product,
                self.version,
                self.account_id,
                self.region,
            ),
        }
        self.assertEqual(expected_result, self.sut.requires())


class ProvisionProductTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "lnklknkl"

    launch_name = "adsfdf"
    portfolio = "port1"
    product = "prod1"
    version = "version1"
    region = "eu-west-0"
    account_id = "09876543211"

    puppet_account_id = "01234567890"

    parameters = list()
    ssm_param_inputs = list()

    launch_parameters = dict()
    manifest_parameters = dict()
    account_parameters = dict()

    retry_count = 1
    worker_timeout = 5
    ssm_param_outputs = list()
    should_use_sns = True
    should_use_product_plans = True
    requested_priority = 1

    execution = "hub"

    def setUp(self) -> None:
        from . import provisioning

        self.sut = provisioning.ProvisionProductTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
            parameters=self.parameters,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            retry_count=self.retry_count,
            worker_timeout=self.worker_timeout,
            ssm_param_outputs=self.ssm_param_outputs,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            requested_priority=self.requested_priority,
            execution=self.execution,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
            "execution": self.execution,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())

    def test_api_calls_used(self):
        expected_result = {
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",
            f"cloudformation.get_template_summary_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioned_product_plans_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.delete_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.create_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.execute_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.provision_product_{self.account_id}_{self.region}",
            # f"ssm.put_parameter_and_wait_{self.region}",
        }
        self.assertEqual(expected_result, self.sut.api_calls_used())


class ProvisionProductDryRunTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "lnklknkl"

    launch_name = "adsfdf"
    portfolio = "port1"
    product = "prod1"
    version = "version1"
    region = "eu-west-0"
    account_id = "09876543211"

    puppet_account_id = "01234567890"

    parameters = list()
    ssm_param_inputs = list()

    launch_parameters = dict()
    manifest_parameters = dict()
    account_parameters = dict()

    retry_count = 1
    worker_timeout = 5
    ssm_param_outputs = list()
    should_use_sns = True
    should_use_product_plans = True
    requested_priority = 1

    execution = "hub"

    def setUp(self) -> None:
        from . import provisioning

        self.sut = provisioning.ProvisionProductDryRunTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
            parameters=self.parameters,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            retry_count=self.retry_count,
            worker_timeout=self.worker_timeout,
            ssm_param_outputs=self.ssm_param_outputs,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            requested_priority=self.requested_priority,
            execution=self.execution,
        )


class TerminateProductTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "lnklknkl"

    launch_name = "adsfdf"
    portfolio = "port1"
    product = "prod1"
    version = "version1"

    account_id = "09876543211"
    region = "eu-west-0"
    puppet_account_id = "01234567890"

    retry_count = 1

    ssm_param_outputs = list()

    worker_timeout = 5

    parameters = list()
    ssm_param_inputs = list()

    def setUp(self) -> None:
        from . import provisioning

        self.sut = provisioning.TerminateProductTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            account_id=self.account_id,
            region=self.region,
            retry_count=self.retry_count,
            ssm_param_outputs=self.ssm_param_outputs,
            worker_timeout=self.worker_timeout,
            parameters=self.parameters,
            ssm_param_inputs=self.ssm_param_inputs,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class TerminateProductDryRunTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "lnklknkl"

    launch_name = "adsfdf"
    portfolio = "port1"
    product = "prod1"
    version = "version1"

    account_id = "09876543211"
    region = "eu-west-0"
    puppet_account_id = "01234567890"

    retry_count = 1

    ssm_param_outputs = list()

    worker_timeout = 5

    parameters = list()
    ssm_param_inputs = list()

    def setUp(self) -> None:
        from . import provisioning

        self.sut = provisioning.TerminateProductDryRunTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            account_id=self.account_id,
            region=self.region,
            retry_count=self.retry_count,
            ssm_param_outputs=self.ssm_param_outputs,
            worker_timeout=self.worker_timeout,
            parameters=self.parameters,
            ssm_param_inputs=self.ssm_param_inputs,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class ResetProvisionedProductOwnerTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "lnklknkl"
    launch_name = "adsfdf"
    account_id = "09876543211"
    region = "eu-west-0"

    def setUp(self) -> None:
        from . import provisioning

        self.sut = provisioning.ResetProvisionedProductOwnerTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            account_id=self.account_id,
            region=self.region,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


class RunDeployInSpokeTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    manifest_file_path = "lnklknkl"
    puppet_account_id = "01234567890"
    account_id = "09876543211"

    home_region = "eu-west-0"
    regions = list()
    should_collect_cloudformation_events = False
    should_forward_events_to_eventbridge = False
    should_forward_failures_to_opscenter = True

    def setUp(self) -> None:
        from . import provisioning

        self.sut = provisioning.RunDeployInSpokeTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
            home_region=self.home_region,
            regions=self.regions,
            should_collect_cloudformation_events=self.should_collect_cloudformation_events,
            should_forward_events_to_eventbridge=self.should_forward_events_to_eventbridge,
            should_forward_failures_to_opscenter=self.should_forward_failures_to_opscenter,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())


#
# class LaunchInSpokeTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import provisioning
#
#         self.sut = provisioning.LaunchInSpokeTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "launch_name": self.launch_name,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class LaunchTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import provisioning
#
#         self.sut = provisioning.LaunchTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "launch_name": self.launch_name,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
#
#
# class SpokeLocalPortfolioTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
#
#     def setUp(self) -> None:
#         from . import provisioning
#
#         self.sut = provisioning.SpokeLocalPortfolioTask(
#         )
#
#     def test_params_for_results_display(self):
#         expected_result = {
#             "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
#         }
#         self.assertEqual(expected_result, self.sut.params_for_results_display())
