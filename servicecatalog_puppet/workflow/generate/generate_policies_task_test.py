#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper
from servicecatalog_puppet import constants
import os


class GeneratePoliciesTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    region = "region"
    sharing_policies = {}

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.generate import generate_policies_task

        self.module = generate_policies_task

        self.sut = self.module.GeneratePolicies(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            region=self.region,
            sharing_policies=self.sharing_policies,
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

    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"cloudformation.create_or_update_{self.puppet_account_id}_{self.region}": 1,
        }

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        template = "foobar"
        self.inject_into_input("template", template)

        # exercise
        os.environ["SCT_INITIALISER_STACK_TAGS"] = "{}"
        self.sut.run()

        # verify
        self.assert_hub_regional_client_called_with(
            "cloudformation",
            "create_or_update",
            dict(
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-policies",
                TemplateBody=template,
                NotificationARNs=[],
                ShouldDeleteRollbackComplete=constants.CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS_DEFAULT,
                Tags={},
            ),
        )
