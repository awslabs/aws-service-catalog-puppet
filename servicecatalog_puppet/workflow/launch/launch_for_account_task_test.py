from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LaunchForAccountTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    launch_name = "launch_name"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import launch_for_account_task

        self.module = launch_for_account_task

        self.sut = self.module.LaunchForAccountTask(
            puppet_account_id=self.puppet_account_id,
            launch_name=self.launch_name,
            account_id=self.account_id,
            manifest_file_path=self.manifest_file_path,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    