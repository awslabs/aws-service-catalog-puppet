from unittest import skip
from . import tasks_unit_tests_helper



class GeneratePoliciesTemplateTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    region = "region"
    sharing_policies = {}
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate
        self.module = generate
        
        self.sut = self.module.GeneratePoliciesTemplate(
            puppet_account_id=self.puppet_account_id, manifest_file_path=self.manifest_file_path, region=self.region, sharing_policies=self.sharing_policies, cache_invalidator=self.cache_invalidator        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
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
    
class EnsureEventBridgeEventBusTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate
        self.module = generate
        
        self.sut = self.module.EnsureEventBridgeEventBusTask(
            puppet_account_id=self.puppet_account_id, region=self.region        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
        }        
    
        # exercise
        actual_result = self.sut.params_for_results_display()
        
        # verify
        self.assertEqual(expected_result, actual_result)
    
    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"events.describe_event_bus_{self.puppet_account_id}_{self.region}": 1,
            f"events.create_event_bus_{self.puppet_account_id}_{self.region}": 1,
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
    
class GeneratePoliciesTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    region = "region"
    sharing_policies = {}
    should_use_sns = False
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate
        self.module = generate
        
        self.sut = self.module.GeneratePolicies(
            puppet_account_id=self.puppet_account_id, manifest_file_path=self.manifest_file_path, region=self.region, sharing_policies=self.sharing_policies, should_use_sns=self.should_use_sns, cache_invalidator=self.cache_invalidator        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "should_use_sns": self.should_use_sns,
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
            f"cloudformation.create_or_update_{self.puppet_account_id}_{self.region}": 1,
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
    
class GenerateSharesTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    should_use_sns = False
    section = "section"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate
        self.module = generate
        
        self.sut = self.module.GenerateSharesTask(
            puppet_account_id=self.puppet_account_id, manifest_file_path=self.manifest_file_path, should_use_sns=self.should_use_sns, section=self.section, cache_invalidator=self.cache_invalidator        
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "section": self.section,
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
    