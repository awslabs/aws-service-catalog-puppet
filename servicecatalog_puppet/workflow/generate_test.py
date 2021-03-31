from unittest import skip
from unittest.mock import MagicMock

from . import tasks_unit_tests_helper


class GeneratePoliciesTemplateTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    region = "region"
    sharing_policies = dict(accounts=["01234567890",], organizations=["ou-0932u0jsdj"],)
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate

        self.module = generate

        self.sut = self.module.GeneratePoliciesTemplate(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            region=self.region,
            sharing_policies=self.sharing_policies,
            cache_invalidator=self.cache_invalidator,
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
        mocked_output().open().__enter__().write.assert_called_with(
            '# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.\n# SPDX-License-Identifier: Apache-2.0\nAWSTemplateFormatVersion: \'2010-09-09\'\nDescription: |\n  Shares for puppet\n  {"version": "0.101.3", "framework": "servicecatalog-puppet", "role": "policies"}\n\nConditions:\n  NoOpCondition: !Equals [ true, false]\n  RunningInHomeRegion: !Equals [ !Ref "AWS::Region", region ]\n\nResources:\n  NoOpResource:\n    Type: AWS::S3::Bucket\n    Description: Resource to ensure that template contains a resource even when there are no shares\n    Condition: NoOpCondition\n\n\n  \n  TopicPolicies:\n    Type: AWS::SNS::TopicPolicy\n    Properties:\n      Topics:\n        - !Sub "arn:${AWS::Partition}:sns:${AWS::Region}:${AWS::AccountId}:servicecatalog-puppet-cloudformation-regional-events"\n      PolicyDocument:\n        Id: MyTopicPolicy\n        Version: \'2012-10-17\'\n        Statement: \n          - Sid: "ShareFor01234567890"\n            Effect: Allow\n            Principal:\n              AWS: !Sub "arn:${AWS::Partition}:iam::01234567890:root"\n            Action: sns:Publish\n            Resource: "*"\n        \n          - Sid: OrganizationalShareForou-0932u0jsdj\n            Action:\n              - sns:Publish\n            Effect: "Allow"\n            Resource: "*"\n            Principal: "*"\n            Condition:\n              StringEquals:\n                aws:PrincipalOrgID: ou-0932u0jsdj\n  \n\n  \n  BucketPolicies:\n    Type: AWS::S3::BucketPolicy\n    Properties:\n      Bucket: !Sub "sc-factory-artifacts-${AWS::AccountId}-${AWS::Region}"\n      PolicyDocument:\n        Statement:\n          - Sid: ShareFor01234567890\n            Action:\n              - "s3:Get*"\n              - "s3:List*"\n            Effect: "Allow"\n            Resource:\n              - !Sub "arn:${AWS::Partition}:s3:::sc-factory-artifacts-${AWS::AccountId}-${AWS::Region}/*"\n              - !Sub "arn:${AWS::Partition}:s3:::sc-factory-artifacts-${AWS::AccountId}-${AWS::Region}"\n            Principal:\n              AWS: !Sub "arn:${AWS::Partition}:iam::01234567890:root"\n        \n          - Sid: OrganizationalShareForou-0932u0jsdj\n            Action:\n              - "s3:Get*"\n              - "s3:List*"\n            Effect: "Allow"\n            Resource:\n              - !Sub "arn:${AWS::Partition}:s3:::sc-factory-artifacts-${AWS::AccountId}-${AWS::Region}/*"\n              - !Sub "arn:${AWS::Partition}:s3:::sc-factory-artifacts-${AWS::AccountId}-${AWS::Region}"\n            Principal: "*"\n            Condition:\n              StringEquals:\n                aws:PrincipalOrgID: ou-0932u0jsdj\n  \n\n  \n  \n  \n  EventBusPolicy01234567890:\n    Type: AWS::Events::EventBusPolicy\n    Condition: RunningInHomeRegion\n    Properties:\n      EventBusName: "servicecatalog-puppet-event-bus"\n      Action: "events:PutEvents"\n      Principal: "01234567890"\n      StatementId: "AllowSpokesAccounts01234567890"\n  \n  \n\n  \n  EventBusPolicyou0932u0jsdj:\n    Type: AWS::Events::EventBusPolicy\n    Condition: RunningInHomeRegion\n    Properties:\n      EventBusName: "servicecatalog-puppet-event-bus"\n      Action: "events:PutEvents"\n      Principal: "*"\n      StatementId: "AllowSpokesOrgsou-0932u0jsdj"\n      Condition:\n        Type: "StringEquals"\n        Key: "aws:PrincipalOrgID"\n        Value: "ou-0932u0jsdj"\n  \n  '
        )


class EnsureEventBridgeEventBusTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate

        self.module = generate

        self.sut = self.module.EnsureEventBridgeEventBusTask(
            puppet_account_id=self.puppet_account_id, region=self.region
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"events.describe_event_bus_{self.puppet_account_id}_{self.region}": 1,
            f"events.create_event_bus_{self.puppet_account_id}_{self.region}": 1,
        }

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_run(self):
        # setup
        from servicecatalog_puppet import constants

        # exercise
        self.sut.run()

        # verify
        self.assert_hub_regional_client_called_with(
            "events", "describe_event_bus", dict(Name=constants.EVENT_BUS_NAME)
        )
        self.assert_output(True)


class GeneratePoliciesTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    region = "region"
    sharing_policies = {}
    should_use_sns = False
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate

        self.module = generate

        self.sut = self.module.GeneratePolicies(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            region=self.region,
            sharing_policies=self.sharing_policies,
            should_use_sns=self.should_use_sns,
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "should_use_sns": self.should_use_sns,
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
            ),
        )


class GenerateSharesTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    should_use_sns = False
    section = "section"
    cache_invalidator = "cache_invalidator"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate

        self.module = generate

        self.sut = self.module.GenerateSharesTask(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            should_use_sns=self.should_use_sns,
            section=self.section,
            cache_invalidator=self.cache_invalidator,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "section": self.section,
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
