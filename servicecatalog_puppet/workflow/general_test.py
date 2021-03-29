from . import tasks_unit_tests_helper



class DeleteCloudFormationStackTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    region = "region"
    stack_name = "stack_name"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import general
        self.module = general
        
        self.sut = self.module.DeleteCloudFormationStackTask(
            account_id=self.account_id, region=self.region, stack_name=self.stack_name        
        )    

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "stack_name": self.stack_name,
            "account_id": self.account_id,
            "region": self.region,
        }        
    
        # exercise
        actual_result = self.sut.params_for_results_display()
        
        # verify
        self.assertEqual(expected_result, actual_result)
    
    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"cloudformation.describe_stacks_single_page_{self.account_id}_{self.region}": 1,
            f"cloudformation.delete_stack_{self.account_id}_{self.region}": 1,
            f"cloudformation.describe_stack_events_{self.account_id}_{self.region}": 1,
        }        
    
        # exercise
        actual_result = self.sut.api_calls_used()
        
        # verify
        self.assertEqual(expected_result, actual_result)
    