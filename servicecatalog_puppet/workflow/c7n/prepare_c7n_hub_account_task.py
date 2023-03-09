#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi
import troposphere as t
import yaml
from troposphere import codebuild, iam, s3

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow.dependencies import tasks


class PrepareC7NHubAccountTask(tasks.TaskWithReferenceAndCommonParameters):
    custodian_region = luigi.Parameter()
    c7n_version = luigi.Parameter()
    organization = luigi.Parameter()
    role_name = luigi.Parameter()
    role_path = luigi.Parameter()

    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
        }

    def run(self):
        # TODO move to troposphere
        template = f"""
  eventbuspolicy:
    Type: AWS::Events::EventBusPolicy
    Properties:
      Condition:
        Key: aws:PrincipalOrgID
        Type: StringEquals
        Value: {self.organization}
      Action: events:PutEvents
      Principal: '*'
      StatementId: OrganizationAccounts
    """
        tpl = t.Template()
        tpl.description = "event bus template for c7n created by service catalog puppet"

        tpl.add_resource(
            iam.Role(
                "C7NRunRole",
                RoleName="C7NRunRole",
                AssumeRolePolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["sts:AssumeRole"],
                            "Effect": "Allow",
                            "Principal": {"Service": ["codebuild.amazonaws.com"]},
                        }
                    ],
                },
                Policies=[
                    iam.Policy(
                        PolicyName="C7NRunRoleActions",
                        PolicyDocument={
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Action": ["sts:AssumeRole",],
                                    "Resource": t.Sub(
                                        "arn:${AWS::Partition}:iam::*:role"
                                        + self.role_path
                                        + self.role_name
                                    ),
                                    "Effect": "Allow",
                                },
                                {
                                    "Action": [
                                        "logs:CreateLogStream",
                                        "logs:CreateLogGroup",
                                        "logs:PutLogEvents",
                                    ],
                                    "Resource": t.Sub(
                                        "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/codebuild/servicecatalog-puppet-deploy-c7n:log-stream:*"
                                    ),
                                    "Effect": "Allow",
                                },
                                {
                                    "Action": ["logs:GetLogEvents",],
                                    "Resource": t.Sub(
                                        "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/codebuild/servicecatalog-puppet-deploy-c7n:log-stream:*"
                                    ),
                                    "Effect": "Allow",
                                },
                            ],
                        },
                    )
                ],
                Path=config.get_puppet_role_path(),
            )
        )

        tpl.add_resource(
            s3.Bucket(
                "c7nPoliciesBucket",
                BucketName=t.Sub(
                    "sc-puppet-c7n-artifacts-${AWS::AccountId}-" + self.custodian_region
                ),
                VersioningConfiguration=s3.VersioningConfiguration(Status="Enabled"),
                BucketEncryption=s3.BucketEncryption(
                    ServerSideEncryptionConfiguration=[
                        s3.ServerSideEncryptionRule(
                            ServerSideEncryptionByDefault=s3.ServerSideEncryptionByDefault(
                                SSEAlgorithm="AES256"
                            )
                        )
                    ]
                ),
                PublicAccessBlockConfiguration=s3.PublicAccessBlockConfiguration(
                    BlockPublicAcls=True,
                    BlockPublicPolicy=True,
                    IgnorePublicAcls=True,
                    RestrictPublicBuckets=True,
                ),
                Tags=t.Tags({"ServiceCatalogPuppet:Actor": "Framework"}),
            )
        )

        tpl.add_resource(
            codebuild.Project(
                "DeployC7N",
                Name="servicecatalog-puppet-deploy-c7n",
                ServiceRole=t.GetAtt("C7NRunRole", "Arn"),
                Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
                Artifacts=codebuild.Artifacts(Type="NO_ARTIFACTS"),
                TimeoutInMinutes=60,
                Environment=codebuild.Environment(
                    ComputeType="BUILD_GENERAL1_SMALL",
                    Image=constants.CODEBUILD_DEFAULT_IMAGE,
                    Type="LINUX_CONTAINER",
                    EnvironmentVariables=[
                        {
                            "Type": "PLAINTEXT",
                            "Name": "C7N_VERSION",
                            "Value": self.c7n_version,
                        },
                        {
                            "Type": "PLAINTEXT",
                            "Name": "POLICIES_FILE_URL",
                            "Value": "CHANGE_ME",
                        },
                        {"Type": "PLAINTEXT", "Name": "REGIONS", "Value": "CHANGE_ME",},
                        {
                            "Type": "PLAINTEXT",
                            "Name": "CUSTODIAN_ROLE_ARN",
                            "Value": "CHANGE_ME",
                        },
                    ],
                ),
                Source=codebuild.Source(
                    BuildSpec=yaml.safe_dump(
                        dict(
                            version=0.2,
                            phases=dict(
                                install={
                                    "commands": ["pip install c7n==${C7N_VERSION}"]
                                },
                                build={
                                    "commands": [
                                        "curl -L ${POLICIES_FILE_URL} > policies.yaml",
                                        "for REGION in ${REGIONS}; do custodian run -s output/logs -r ${REGION} --assume ${CUSTODIAN_ROLE_ARN} policies.yaml; done",
                                    ]
                                },
                            ),
                        )
                    ),
                    Type="NO_SOURCE",
                ),
                Description="Run c7n",
            )
        )

        template = tpl.to_yaml() + template

        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.create_or_update(
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-c7n-eventbus",
                Capabilities=["CAPABILITY_NAMED_IAM"],
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )
        self.write_output(dict(c7n_account_id=self.account_id,))
