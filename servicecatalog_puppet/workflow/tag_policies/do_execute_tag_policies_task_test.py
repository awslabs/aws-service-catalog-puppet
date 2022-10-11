from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoExecuteTagPoliciesTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    tag_policy_name = "tag_policy_name"
    region = "region"
    account_id = "account_id"
    ou_name = "ou_name"
    content = {}
    description = "description"
    manifest_file_path = "manifest_file_path"
    requested_priority = 1
    get_or_create_policy_ref = "get_or_create_policy_ref"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.tag_policies import (
            do_execute_tag_policies_task,
        )

        self.module = do_execute_tag_policies_task

        self.sut = self.module.DoExecuteTagPoliciesTask(
            **self.get_common_args(),
            tag_policy_name=self.tag_policy_name,
            region=self.region,
            account_id=self.account_id,
            ou_name=self.ou_name,
            content=self.content,
            description=self.description,
            manifest_file_path=self.manifest_file_path,
            requested_priority=self.requested_priority,
            get_or_create_policy_ref=self.get_or_create_policy_ref,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "tag_policy_name": self.tag_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "ou_name": self.ou_name,
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
