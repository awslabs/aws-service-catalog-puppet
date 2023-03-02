import luigi
import troposphere as t
from awacs.aws import Statement
from troposphere import s3

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow.dependencies import tasks


class ForwardEventsTask(tasks.TaskWithReferenceAndCommonParameters):
    create_event_bus_task_ref = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "region": self.region,
            "account_id": self.account_id,
        }

    def run(self):
        c7n_account_id = self.get_attribute_from_output_from_reference_dependency(
            "c7n_account_id", self.create_event_bus_task_ref
        )
        role_name = self.get_attribute_from_output_from_reference_dependency(
            "role_name", self.create_event_bus_task_ref
        )
        role_path = self.get_attribute_from_output_from_reference_dependency(
            "role_path", self.create_event_bus_task_ref
        )
        role_managed_policy_arns = self.get_attribute_from_output_from_reference_dependency(
            "role_managed_policy_arns", self.create_event_bus_task_ref
        )

        tpl = t.Template()
        tpl.description = (
            "event forwarder template for c7n created by service catalog puppet"
        )
        tpl.add_resource(
            s3.Bucket(
                "c7nTrailBucket",
                PublicAccessBlockConfiguration=s3.PublicAccessBlockConfiguration(
                    BlockPublicAcls=True,
                    BlockPublicPolicy=True,
                    IgnorePublicAcls=True,
                    RestrictPublicBuckets=True,
                ),
                BucketEncryption=s3.BucketEncryption(
                    ServerSideEncryptionConfiguration=[
                        s3.ServerSideEncryptionRule(
                            ServerSideEncryptionByDefault=s3.ServerSideEncryptionByDefault(
                                SSEAlgorithm="AES256"
                            )
                        )
                    ]
                ),
                VersioningConfiguration=s3.VersioningConfiguration(Status="Enabled"),
            )
        )

        tpl.add_resource(
            s3.BucketPolicy(
                "c7nTrailBucketPolicy",
                Bucket=t.Ref("c7nTrailBucket"),
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["s3:GetBucketAcl",],
                            "Principal": {"Service": "cloudtrail.amazonaws.com"},
                            "Resource": t.GetAtt("c7nTrailBucket", "Arn"),
                            "Effect": "Allow",
                            "Sid": "AWSCloudTrailAclCheck",
                        },
                        {
                            "Action": ["s3:PutObject",],
                            "Principal": {"Service": "cloudtrail.amazonaws.com"},
                            "Resource": t.Sub(
                                "arn:${AWS::Partition}:s3:::${c7nTrailBucket}/AWSLogs/${AWS::AccountId}/*"
                            ),
                            "Effect": "Allow",
                            "Sid": "AWSCloudTrailWrite",
                            "Condition": {
                                "StringEquals": {
                                    "s3:x-amz-acl": "bucket-owner-full-control"
                                }
                            },
                        },
                    ],
                },
            )
        )
        template = tpl.to_yaml()
        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.create_or_update(
                Capabilities=["CAPABILITY_NAMED_IAM"],
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-c7n-eventforwarding",
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )
        self.write_empty_output()
