from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class AssertTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    assertion_name = "assertion_name"
    region = "region"
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    expected = {}
    actual = {}
    requested_priority = 1

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.assertions import assert_task
        self.module = assert_task
        
        self.sut = self.module.AssertTask(
            manifest_file_path=self.manifest_file_path, assertion_name=self.assertion_name, region=self.region, account_id=self.account_id, puppet_account_id=self.puppet_account_id, expected=self.expected, actual=self.actual, requested_priority=self.requested_priority
        )
        
        self.wire_up_mocks()    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "region": self.region,
            "account_id": self.account_id,
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
    