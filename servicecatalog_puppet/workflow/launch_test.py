from unittest import skip

from . import tasks_unit_tests_helper


class LaunchSectionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.LaunchSectionTask(
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
        self.assertDictEqual(expected_result, actual_result)

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


class ProvisioningTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

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
    product = "product"
    version = "version"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.ProvisioningArtifactParametersTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "product": self.product,
            "version": self.version,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = []

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


class DoProvisionProductTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    portfolio = "portfolio"
    product = "product"
    version = "version"
    region = "region"
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    retry_count = 1
    worker_timeout = 3
    ssm_param_outputs = []

    requested_priority = 1
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.DoProvisionProductTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            retry_count=self.retry_count,
            worker_timeout=self.worker_timeout,
            ssm_param_outputs=self.ssm_param_outputs,
            requested_priority=self.requested_priority,
            execution=self.execution,
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

    @skip
    def test_requires(self):
        # setup
        # exercise
        actual_result = self.sut.requires()

        # verify
        raise NotImplementedError()

    def test_api_calls_used(self):
        # setup
        expected_result = [
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
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
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


class ProvisionProductDryRunTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    portfolio = "portfolio"
    product = "product"
    version = "version"
    region = "region"
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    retry_count = 1
    worker_timeout = 3
    ssm_param_outputs = []
    should_use_sns = False

    requested_priority = 1
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.ProvisionProductDryRunTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            retry_count=self.retry_count,
            worker_timeout=self.worker_timeout,
            ssm_param_outputs=self.ssm_param_outputs,
            requested_priority=self.requested_priority,
            execution=self.execution,
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
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.TerminateProductTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            account_id=self.account_id,
            region=self.region,
            puppet_account_id=self.puppet_account_id,
            retry_count=self.retry_count,
            ssm_param_outputs=self.ssm_param_outputs,
            worker_timeout=self.worker_timeout,
            ssm_param_inputs=self.ssm_param_inputs,
            execution=self.execution,
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

    def test_api_calls_used(self):
        # setup
        expected_result = []

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

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

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


class ResetProvisionedProductOwnerTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    account_id = "account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

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

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.RunDeployInSpokeTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "cache_invalidator": "NOW",
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertDictEqual(expected_result, actual_result)

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

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.LaunchInSpokeTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
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


class LaunchTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    puppet_account_id = "puppet_account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import launch

        self.module = launch

        self.sut = self.module.LaunchTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertDictEqual(expected_result, actual_result)

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
