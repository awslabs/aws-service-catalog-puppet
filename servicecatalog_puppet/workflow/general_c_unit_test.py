from . import tasks_unit_tests


class DeleteCloudFormationStackTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    account_id = "0123456789010"
    region = "eu-west-0"
    stack_name = "foo"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import general

        self.module = general
        self.sut = self.module.DeleteCloudFormationStackTask(
            account_id=self.account_id, region=self.region, stack_name=self.stack_name,
        )

    def test_params_for_results_display(self):
        expected_result = {
            "account_id": self.account_id,
            "region": self.region,
            "stack_name": self.stack_name,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())

    def test_api_calls_used(self):
        expected_result = {
            f"cloudformation.describe_stacks_single_page_{self.account_id}_{self.region}": 1,
            f"cloudformation.delete_stack_{self.account_id}_{self.region}": 1,
            f"cloudformation.describe_stack_events_{self.account_id}_{self.region}": 1,
        }
        self.assertEqual(expected_result, self.sut.api_calls_used())
