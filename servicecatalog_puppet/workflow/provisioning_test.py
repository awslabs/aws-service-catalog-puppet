from unittest import skip
from . import tasks_unit_tests_helper


class ProvisioningTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.ProvisioningTask(
            manifest_file_path=self.manifest_file_path
        )

        self.wire_up_mocks()


class ProvisioningArtifactParametersTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    portfolio = "portfolio"
    portfolio_id = "portfolio_id"
    product = "product"
    product_id = "product_id"
    version = "version"
    version_id = "version_id"
    account_id = "account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.ProvisioningArtifactParametersTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
            product=self.product,
            product_id=self.product_id,
            version=self.version,
            version_id=self.version_id,
            account_id=self.account_id,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "account_id": self.account_id,
            "region": self.region,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_parameters_{self.account_id}_{self.region}",
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


class ProvisionProductTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    portfolio = "portfolio"
    portfolio_id = "portfolio_id"
    product = "product"
    product_id = "product_id"
    version = "version"
    version_id = "version_id"
    region = "region"
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    parameters = {}
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    retry_count = 1
    worker_timeout = 3
    ssm_param_outputs = []
    should_use_sns = False
    should_use_product_plans = False
    requested_priority = 1
    execution = "execution"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.ProvisionProductTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
            product=self.product,
            product_id=self.product_id,
            version=self.version,
            version_id=self.version_id,
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
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "execution": self.execution,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_requires(self):
        # setup
        # exercise
        actual_result = self.sut.requires()

        # verify
        raise NotImplementedError()

    def test_api_calls_used(self):
        # setup
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


class ProvisionProductDryRunTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    portfolio = "portfolio"
    portfolio_id = "portfolio_id"
    product = "product"
    product_id = "product_id"
    version = "version"
    version_id = "version_id"
    region = "region"
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    parameters = {}
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    retry_count = 1
    worker_timeout = 3
    ssm_param_outputs = []
    should_use_sns = False
    should_use_product_plans = False
    requested_priority = 1
    execution = "execution"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.ProvisionProductDryRunTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
            product=self.product,
            product_id=self.product_id,
            version=self.version,
            version_id=self.version_id,
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
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",
            f"cloudformation.describe_provisioning_artifact_{self.account_id}_{self.region}",
            f"cloudformation.get_template_summary_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
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


class TerminateProductTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
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
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.TerminateProductTask(
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
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.scan_provisioned_products_single_page{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",
            # f"ssm.delete_parameter_{self.region}": 1,
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
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

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
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

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


class ResetProvisionedProductOwnerTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    account_id = "account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.ResetProvisionedProductOwnerTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            account_id=self.account_id,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_properties_{self.account_id}_{self.region}",
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


class RunDeployInSpokeTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    account_id = "account_id"
    home_region = "home_region"
    regions = []
    should_collect_cloudformation_events = False
    should_forward_events_to_eventbridge = False
    should_forward_failures_to_opscenter = False

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.RunDeployInSpokeTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
            home_region=self.home_region,
            regions=self.regions,
            should_collect_cloudformation_events=self.should_collect_cloudformation_events,
            should_forward_events_to_eventbridge=self.should_forward_events_to_eventbridge,
            should_forward_failures_to_opscenter=self.should_forward_failures_to_opscenter,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
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


class LaunchInSpokeTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    execution_mode = "execution_mode"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.LaunchInSpokeTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            puppet_account_id=self.puppet_account_id,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            include_expanded_from=self.include_expanded_from,
            single_account=self.single_account,
            is_dry_run=self.is_dry_run,
            execution_mode=self.execution_mode,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "launch_name": self.launch_name,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_requires(self):
        # setup
        # exercise
        actual_result = self.sut.requires()

        # verify
        raise NotImplementedError()

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()


class LaunchTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    execution_mode = "execution_mode"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.LaunchTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            puppet_account_id=self.puppet_account_id,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            include_expanded_from=self.include_expanded_from,
            single_account=self.single_account,
            is_dry_run=self.is_dry_run,
            execution_mode=self.execution_mode,
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "launch_name": self.launch_name,
            "execution_mode": self.execution_mode,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_requires(self):
        # setup
        # exercise
        actual_result = self.sut.requires()

        # verify
        raise NotImplementedError()

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()


class SpokeLocalPortfolioTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    depends_on = []
    sharing_mode = "sharing_mode"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import provisioning

        self.module = provisioning

        self.sut = self.module.SpokeLocalPortfolioTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            puppet_account_id=self.puppet_account_id,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            include_expanded_from=self.include_expanded_from,
            single_account=self.single_account,
            is_dry_run=self.is_dry_run,
            depends_on=self.depends_on,
            sharing_mode=self.sharing_mode,
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "sharing_mode": self.sharing_mode,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_requires(self):
        # setup
        # exercise
        actual_result = self.sut.requires()

        # verify
        raise NotImplementedError()

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
