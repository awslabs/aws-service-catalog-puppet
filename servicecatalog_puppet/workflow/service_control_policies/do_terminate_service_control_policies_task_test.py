from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoTerminateServiceControlPoliciesTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    service_control_policy_name = "service_control_policy_name"
    region = "region"
    account_id = "account_id"
    ou_name = "ou_name"
    content = {}
    description = "description"
    manifest_file_path = "manifest_file_path"
    requested_priority = 1

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.service_control_policies import (
            do_terminate_service_control_policies_task,
        )

        self.module = do_terminate_service_control_policies_task

        self.sut = self.module.DoTerminateServiceControlPoliciesTask(
            **self.get_common_args(),
            service_control_policy_name=self.service_control_policy_name,
            region=self.region,
            account_id=self.account_id,
            ou_name=self.ou_name,
            content=self.content,
            description=self.description,
            manifest_file_path=self.manifest_file_path,
            requested_priority=self.requested_priority,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "service_control_policy_name": self.service_control_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "ou_name": self.ou_name,
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
