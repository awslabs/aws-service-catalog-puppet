import unittest


class DeleteCloudFormationStackTaskComponentTest(unittest.TestCase):
    account_id = "0123456789010"
    region = "eu-west-0"
    stack_name = "delete-me"

    def setUp(self) -> None:
        from . import general

        self.sut = general.DeleteCloudFormationStackTask(
            self.account_id, self.region, self.stack_name
        )

    def test_params_for_results_display(self):
        self.assertEqual(
            {
                "account_id": self.account_id,
                "region": self.region,
                "stack_name": self.stack_name,
            },
            self.sut.params_for_results_display(),
        )

    def test_api_calls_used(self):
        self.assertEqual(
            {
                f"cloudformation.describe_stacks_single_page_{self.account_id}_{self.region}": 1,
                f"cloudformation.delete_stack_{self.account_id}_{self.region}": 1,
                f"cloudformation.describe_stack_events_{self.account_id}_{self.region}": 1,
            },
            self.sut.api_calls_used(),
        )
