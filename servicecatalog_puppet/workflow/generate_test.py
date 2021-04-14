from unittest import skip
from unittest.mock import MagicMock

from cfn_tools import load_yaml, dump_yaml

from . import tasks_unit_tests_helper


class GeneratePoliciesTemplateTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    region = "region"
    sharing_policies = dict(accounts=["01234567890",], organizations=["ou-0932u0jsdj"],)

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate

        self.module = generate

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
                Condition="RunningInHomeRegion",
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
                Condition="RunningInHomeRegion",
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

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate

        self.module = generate

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
    section = "section"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import generate

        self.module = generate

        self.sut = self.module.GenerateSharesTask(
            puppet_account_id=self.puppet_account_id,
            manifest_file_path=self.manifest_file_path,
            section=self.section,
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
