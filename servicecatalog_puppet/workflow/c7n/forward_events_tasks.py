import luigi
import troposphere as t
from troposphere import cloudtrail, events, iam, s3

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow.dependencies import tasks


c7nTrailBucket = "c7nTrailBucket"


class ForwardEventsTask(tasks.TaskWithReferenceAndCommonParameters):
    c7n_account_id = luigi.Parameter()
    event_bus_name = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "region": self.region,
            "account_id": self.account_id,
        }

    def run(self):
        tpl = t.Template()
        tpl.description = (
            "event forwarder template for c7n created by service catalog puppet"
        )
        tpl.add_resource(
            s3.Bucket(
                c7nTrailBucket,
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
                Bucket=t.Ref(c7nTrailBucket),
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["s3:GetBucketAcl",],
                            "Principal": {"Service": "cloudtrail.amazonaws.com"},
                            "Resource": t.GetAtt(c7nTrailBucket, "Arn"),
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

        tpl.add_resource(
            cloudtrail.Trail(
                "c7nTrail",
                S3BucketName=t.Ref(c7nTrailBucket),
                IsLogging=True,
                IsMultiRegionTrail=True,
                IncludeGlobalServiceEvents=True,
            )
        )

        tpl.add_resource(
            iam.Role(
                "c7nEventForwarder",
                RoleName="c7nEventForwarder",
                Path="/servicecatalog-puppet/c7n/",
                Policies=[
                    iam.Policy(
                        PolicyName="AllowPutEvents",
                        PolicyDocument={
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Action": ["events:PutEvents"],
                                    "Resource": {
                                        "Fn::Sub": "arn:${AWS::Partition}:events:${AWS::Region}:"
                                        + self.c7n_account_id
                                        + ":event-bus/"
                                        + self.event_bus_name
                                    },
                                    "Effect": "Allow",
                                }
                            ],
                        },
                    )
                ],
                AssumeRolePolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["sts:AssumeRole"],
                            "Effect": "Allow",
                            "Principal": {"Service": ["events.amazonaws.com"]},
                        },
                        {
                            "Action": ["sts:AssumeRole"],
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": t.Sub(
                                    "arn:${AWS::Partition}:iam::"
                                    + self.c7n_account_id
                                    + ":root"
                                )
                            },
                        },
                    ],
                },
            )
        )

        tpl.add_resource(
            events.Rule(
                "ForwardAll",
                Description="Forward all events for c7n to do its job",
                EventPattern={
                    "detail-type": ["AWS API Call via CloudTrail"],
                    "detail": {"eventSource": ["cloudtrail.amazonaws.com"]},
                },
                State="ENABLED",
                Targets=[
                    events.Target(
                        Arn=t.Sub(
                            "arn:${AWS::Partition}:events:${AWS::Region}:"
                            + self.c7n_account_id
                            + ":event-bus/"
                            + self.event_bus_name
                        ),
                        Id="CloudCustodianHubEventBusArn",
                        RoleArn=t.GetAtt("c7nEventForwarder", "Arn"),
                    )
                ],
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
