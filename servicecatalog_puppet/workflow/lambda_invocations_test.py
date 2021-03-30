from unittest import skip
from . import tasks_unit_tests_helper



class InvokeLambdaTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    lambda_invocation_name = "lambda_invocation_name"
    region = "region"
    account_id = "account_id"
    function_name = "function_name"
    qualifier = "qualifier"
    invocation_type = "invocation_type"
    puppet_account_id = "puppet_account_id"
    parameters = {}
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    manifest_file_path = "manifest_file_path"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import lambda_invocations
        self.module = lambda_invocations
        
        self.sut = self.module.InvokeLambdaTask(
            lambda_invocation_name=self.lambda_invocation_name, region=self.region, account_id=self.account_id, function_name=self.function_name, qualifier=self.qualifier, invocation_type=self.invocation_type, puppet_account_id=self.puppet_account_id, parameters=self.parameters, launch_parameters=self.launch_parameters, manifest_parameters=self.manifest_parameters, account_parameters=self.account_parameters, manifest_file_path=self.manifest_file_path, should_use_sns=self.should_use_sns, should_use_product_plans=self.should_use_product_plans, include_expanded_from=self.include_expanded_from, single_account=self.single_account, is_dry_run=self.is_dry_run, cache_invalidator=self.cache_invalidator        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "lambda_invocation_name": self.lambda_invocation_name,
            "account_id": self.account_id,
            "region": self.region,
            "function_name": self.function_name,
            "qualifier": self.qualifier,
            "invocation_type": self.invocation_type,
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
    
class LambdaInvocationDependenciesWrapperTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    lambda_invocation_name = "lambda_invocation_name"
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import lambda_invocations
        self.module = lambda_invocations
        
        self.sut = self.module.LambdaInvocationDependenciesWrapperTask(
            lambda_invocation_name=self.lambda_invocation_name, manifest_file_path=self.manifest_file_path, puppet_account_id=self.puppet_account_id, should_use_sns=self.should_use_sns, should_use_product_plans=self.should_use_product_plans, include_expanded_from=self.include_expanded_from, single_account=self.single_account, is_dry_run=self.is_dry_run, cache_invalidator=self.cache_invalidator        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "lambda_invocation_name": self.lambda_invocation_name,
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
    
class LambdaInvocationTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    lambda_invocation_name = "lambda_invocation_name"
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import lambda_invocations
        self.module = lambda_invocations
        
        self.sut = self.module.LambdaInvocationTask(
            lambda_invocation_name=self.lambda_invocation_name, manifest_file_path=self.manifest_file_path, puppet_account_id=self.puppet_account_id, should_use_sns=self.should_use_sns, should_use_product_plans=self.should_use_product_plans, include_expanded_from=self.include_expanded_from, single_account=self.single_account, is_dry_run=self.is_dry_run, cache_invalidator=self.cache_invalidator        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "lambda_invocation_name": self.lambda_invocation_name,
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
    
class LambdaInvocationsSectionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    should_use_sns = False
    should_use_product_plans = False
    include_expanded_from = False
    single_account = "single_account"
    is_dry_run = False
    execution_mode = "execution_mode"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import lambda_invocations
        self.module = lambda_invocations
        
        self.sut = self.module.LambdaInvocationsSectionTask(
            manifest_file_path=self.manifest_file_path, puppet_account_id=self.puppet_account_id, should_use_sns=self.should_use_sns, should_use_product_plans=self.should_use_product_plans, include_expanded_from=self.include_expanded_from, single_account=self.single_account, is_dry_run=self.is_dry_run, execution_mode=self.execution_mode, cache_invalidator=self.cache_invalidator        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
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
    