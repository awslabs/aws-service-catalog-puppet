from unittest import skip
from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GetCloudFormationTemplateFromS3Test(tasks_unit_tests_helper.PuppetTaskUnitTest):
    account_id = "account_id"
    bucket = "bucket"
    key = "key"
    region = "region"
    version_id = "version_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.stack import (
            get_cloud_formation_template_from_s3,
        )

        self.module = get_cloud_formation_template_from_s3

        self.sut = self.module.GetCloudFormationTemplateFromS3(
            **self.get_common_args(),
            account_id=self.account_id,
            bucket=self.bucket,
            key=self.key,
            region=self.region,
            version_id=self.version_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "task_reference": self.task_reference,
            "bucket": self.bucket,
            "key": self.key.replace("-${AWS::Region}", f"-{self.region}"),
            "region": self.region,
            "version_id": self.version_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
