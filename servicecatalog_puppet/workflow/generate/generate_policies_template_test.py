#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

from cfn_tools import load_yaml, dump_yaml

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GeneratePoliciesTemplateTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    region = "region"
    sharing_policies = dict(accounts=["01234567890",], organizations=["ou-0932u0jsdj"],)

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.generate import (
            generate_policies_template_task,
        )

        self.module = generate_policies_template_task

        self.sut = self.module.GeneratePoliciesTemplate(
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

    def test_run(self):
        # setup
        mocked_output = MagicMock()
        self.sut.output = mocked_output

        # exercise
        self.sut.run()

        # verify
        template = load_yaml(
            mocked_output().open().__enter__().write.mock_calls[0][1][0]
        )
        found = 0
        statements = (
            template.get("Resources")
            .get("TopicPolicies")
            .get("Properties")
            .get("PolicyDocument")
            .get("Statement", [])
        )
        for statement in statements:
            if statement.get("Sid") == "ShareFor01234567890":
                found += 1
                self.assertEqual(
                    "Fn::Sub: arn:${AWS::Partition}:iam::01234567890:root",
                    dump_yaml(statement.get("Principal").get("AWS")).strip(),
                )

            if statement.get("Sid") == "OrganizationalShareForou-0932u0jsdj":
                found += 1
                self.assertEqual(
                    "ou-0932u0jsdj",
                    statement.get("Condition")
                    .get("StringEquals")
                    .get("aws:PrincipalOrgID"),
                )

        statements = (
            template.get("Resources")
            .get("BucketPolicies")
            .get("Properties")
            .get("PolicyDocument")
            .get("Statement", [])
        )
        for statement in statements:
            if statement.get("Sid") == "ShareFor01234567890":
                found += 1
                self.assertEqual(
                    "Fn::Sub: arn:${AWS::Partition}:iam::01234567890:root",
                    dump_yaml(statement.get("Principal").get("AWS")).strip(),
                )

            if statement.get("Sid") == "OrganizationalShareForou-0932u0jsdj":
                found += 1
                self.assertEqual(
                    "ou-0932u0jsdj",
                    statement.get("Condition")
                    .get("StringEquals")
                    .get("aws:PrincipalOrgID"),
                )

        self.assertDictEqual(
            dict(
                Type="AWS::Events::EventBusPolicy",
                Properties=dict(
                    EventBusName="servicecatalog-puppet-event-bus",
                    Action="events:PutEvents",
                    Principal="01234567890",
                    StatementId="AllowSpokesAccounts01234567890",
                ),
            ),
            template.get("Resources").get(f"EventBusPolicy01234567890"),
        )

        self.assertDictEqual(
            dict(
                Type="AWS::Events::EventBusPolicy",
                Properties=dict(
                    EventBusName="servicecatalog-puppet-event-bus",
                    Action="events:PutEvents",
                    Principal="*",
                    StatementId="AllowSpokesOrgsou-0932u0jsdj",
                    Condition=dict(
                        Type="StringEquals",
                        Key="aws:PrincipalOrgID",
                        Value="ou-0932u0jsdj",
                    ),
                ),
            ),
            template.get("Resources").get(f"EventBusPolicyou0932u0jsdj"),
        )

        self.assertEqual(4, found)
