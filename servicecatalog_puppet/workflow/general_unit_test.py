from . import tasks_unit_tests
from unittest import mock


class DeleteCloudFormationStackTaskTest(tasks_unit_tests.PuppetTaskUnitTest):
    account_id = "0123456789010"
    region = "eu-west-0"
    stack_name = "foo"

    def setUp(self) -> None:
        super().setUp()
        from servicecatalog_puppet.workflow import general

        self.module = general
        self.sut = self.module.DeleteCloudFormationStackTask(
            account_id=self.account_id, region=self.region, stack_name=self.stack_name,
        )

    @mock.patch("servicecatalog_puppet.workflow.general.betterboto_client")
    def test_run(self, mock):
        # setup
        expected_output = "hello world"

        self.expect_call(
            mock,
            dict(
                service="cloudformation",
                role=f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
                session=f"{self.account_id}-{self.region}-PuppetRole",
                region_name=self.region,
            ),
            "ensure_deleted",
            {"StackName": self.stack_name},
            expected_output,
        )

        # exercise
        self.sut.run()

        # verify
        self.verify(mock)
        self.verify_output(self.sut.params_for_results_display())
