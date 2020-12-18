from . import tasks_unit_tests


class BootstrapSpokeAsTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    puppet_account_id = "230947938752"
    account_id = "23948yr59843y5"
    iam_role_arns = list()
    role_name = "goo"
    permission_boundary = "dfojsfdfds"

    def setUp(self) -> None:
        from . import management

        self.sut = management.BootstrapSpokeAsTask(
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
            iam_role_arns=self.iam_role_arns,
            role_name=self.role_name,
            permission_boundary=self.permission_boundary,
            puppet_role_name="PuppetRole",
            puppet_role_path="/servicecatalog-puppet/",
        )

    def test_params_for_results_display(self):
        expected_result = {
            "account_id": self.account_id,
        }
        self.assertEqual(expected_result, self.sut.params_for_results_display())
