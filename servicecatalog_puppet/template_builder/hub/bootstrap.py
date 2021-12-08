#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import troposphere as t
import yaml
from awacs import iam as awscs_iam
from troposphere import codebuild
from troposphere import codecommit
from troposphere import codepipeline
from troposphere import iam
from troposphere import s3
from troposphere import sns
from troposphere import sqs
from troposphere import ssm

from servicecatalog_puppet import constants


def get_template(
    puppet_version,
    all_regions,
    source,
    is_caching_enabled,
    is_manual_approvals: bool,
    scm_skip_creation_of_repo: bool,
    should_validate: bool,
) -> t.Template:
    is_codecommit = source.get("Provider", "").lower() == "codecommit"
    is_github = source.get("Provider", "").lower() == "github"
    is_codestarsourceconnection = (
        source.get("Provider", "").lower() == "codestarsourceconnection"
    )
    is_custom = source.get("Provider", "").lower() == "custom"
    is_s3 = source.get("Provider", "").lower() == "s3"
    description = f"""Bootstrap template used to bring up the main ServiceCatalog-Puppet AWS CodePipeline with dependencies
{{"version": "{puppet_version}", "framework": "servicecatalog-puppet", "role": "bootstrap-master"}}"""

    template = t.Template(Description=description)

    version_parameter = template.add_parameter(
        t.Parameter("Version", Default=puppet_version, Type="String")
    )
    org_iam_role_arn_parameter = template.add_parameter(
        t.Parameter("OrgIamRoleArn", Default="None", Type="String")
    )
    with_manual_approvals_parameter = template.add_parameter(
        t.Parameter(
            "WithManualApprovals",
            Type="String",
            AllowedValues=["Yes", "No"],
            Default="No",
        )
    )
    puppet_code_pipeline_role_permission_boundary_parameter = template.add_parameter(
        t.Parameter(
            "PuppetCodePipelineRolePermissionBoundary",
            Type="String",
            Description="IAM Permission Boundary to apply to the PuppetCodePipelineRole",
            Default=awscs_iam.ARN(resource="policy/AdministratorAccess").data,
        )
    )
    source_role_permissions_boundary_parameter = template.add_parameter(
        t.Parameter(
            "SourceRolePermissionsBoundary",
            Type="String",
            Description="IAM Permission Boundary to apply to the SourceRole",
            Default=awscs_iam.ARN(resource="policy/AdministratorAccess").data,
        )
    )
    puppet_generate_role_permission_boundary_parameter = template.add_parameter(
        t.Parameter(
            "PuppetGenerateRolePermissionBoundary",
            Type="String",
            Description="IAM Permission Boundary to apply to the PuppetGenerateRole",
            Default=awscs_iam.ARN(resource="policy/AdministratorAccess").data,
        )
    )
    puppet_deploy_role_permission_boundary_parameter = template.add_parameter(
        t.Parameter(
            "PuppetDeployRolePermissionBoundary",
            Type="String",
            Description="IAM Permission Boundary to apply to the PuppetDeployRole",
            Default=awscs_iam.ARN(resource="policy/AdministratorAccess").data,
        )
    )
    puppet_provisioning_role_permissions_boundary_parameter = template.add_parameter(
        t.Parameter(
            "PuppetProvisioningRolePermissionsBoundary",
            Type="String",
            Description="IAM Permission Boundary to apply to the PuppetProvisioningRole",
            Default=awscs_iam.ARN(resource="policy/AdministratorAccess").data,
        )
    )
    cloud_formation_deploy_role_permissions_boundary_parameter = template.add_parameter(
        t.Parameter(
            "CloudFormationDeployRolePermissionsBoundary",
            Type="String",
            Description="IAM Permission Boundary to apply to the CloudFormationDeployRole",
            Default=awscs_iam.ARN(resource="policy/AdministratorAccess").data,
        )
    )
    deploy_environment_compute_type_parameter = template.add_parameter(
        t.Parameter(
            "DeployEnvironmentComputeType",
            Type="String",
            Description="The AWS CodeBuild Environment Compute Type",
            Default="BUILD_GENERAL1_SMALL",
        )
    )
    spoke_deploy_environment_compute_type_parameter = template.add_parameter(
        t.Parameter(
            "SpokeDeployEnvironmentComputeType",
            Type="String",
            Description="The AWS CodeBuild Environment Compute Type for spoke execution mode",
            Default="BUILD_GENERAL1_SMALL",
        )
    )
    deploy_num_workers_parameter = template.add_parameter(
        t.Parameter(
            "DeployNumWorkers",
            Type="Number",
            Description="Number of workers that should be used when running a deploy",
            Default=10,
        )
    )
    puppet_role_name_parameter = template.add_parameter(
        t.Parameter("PuppetRoleName", Type="String", Default="PuppetRole")
    )
    puppet_role_path_template_parameter = template.add_parameter(
        t.Parameter("PuppetRolePath", Type="String", Default="/servicecatalog-puppet/")
    )

    template.add_condition(
        "ShouldUseOrgs", t.Not(t.Equals(t.Ref(org_iam_role_arn_parameter), "None"))
    )
    template.add_condition(
        "HasManualApprovals", t.Equals(t.Ref(with_manual_approvals_parameter), "Yes")
    )

    template.add_resource(
        s3.Bucket(
            "StacksRepository",
            BucketName=t.Sub("sc-puppet-stacks-repository-${AWS::AccountId}"),
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

    manual_approvals_param = template.add_resource(
        ssm.Parameter(
            "ManualApprovalsParam",
            Type="String",
            Name="/servicecatalog-puppet/manual-approvals",
            Value=t.Ref(with_manual_approvals_parameter),
        )
    )
    template.add_resource(
        ssm.Parameter(
            "SpokeDeployEnvParameter",
            Type="String",
            Name=constants.SPOKE_EXECUTION_MODE_DEPLOY_ENV_PARAMETER_NAME,
            Value=t.Ref(spoke_deploy_environment_compute_type_parameter),
        )
    )
    param = template.add_resource(
        ssm.Parameter(
            "Param",
            Type="String",
            Name="service-catalog-puppet-version",
            Value=t.Ref(version_parameter),
        )
    )
    partition_parameter = template.add_resource(
        ssm.Parameter(
            "PartitionParameter",
            Type="String",
            Name="/servicecatalog-puppet/partition",
            Value=t.Ref("AWS::Partition"),
        )
    )
    puppet_role_name_parameter = template.add_resource(
        ssm.Parameter(
            "PuppetRoleNameParameter",
            Type="String",
            Name="/servicecatalog-puppet/puppet-role/name",
            Value=t.Ref(puppet_role_name_parameter),
        )
    )
    puppet_role_path_parameter = template.add_resource(
        ssm.Parameter(
            "PuppetRolePathParameter",
            Type="String",
            Name="/servicecatalog-puppet/puppet-role/path",
            Value=t.Ref(puppet_role_path_template_parameter),
        )
    )
    share_accept_function_role = template.add_resource(
        iam.Role(
            "ShareAcceptFunctionRole",
            RoleName="ShareAcceptFunctionRole",
            ManagedPolicyArns=[
                t.Sub(
                    "arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            Path=t.Ref(puppet_role_path_template_parameter),
            Policies=[
                iam.Policy(
                    PolicyName="ServiceCatalogActions",
                    PolicyDocument={
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Action": ["sts:AssumeRole"],
                                "Resource": {
                                    "Fn::Sub": "arn:${AWS::Partition}:iam::*:role${PuppetRolePath}${PuppetRoleName}"
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
                        "Principal": {"Service": ["lambda.amazonaws.com"]},
                    }
                ],
            },
        )
    )

    provisioning_role = template.add_resource(
        iam.Role(
            "ProvisioningRole",
            RoleName="PuppetProvisioningRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"Service": ["codebuild.amazonaws.com"]},
                    },
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"AWS": {"Fn::Sub": "${AWS::AccountId}"}},
                    },
                ],
            },
            ManagedPolicyArns=[
                t.Sub("arn:${AWS::Partition}:iam::aws:policy/AdministratorAccess")
            ],
            PermissionsBoundary=t.Ref(
                puppet_provisioning_role_permissions_boundary_parameter
            ),
            Path=t.Ref(puppet_role_path_template_parameter),
        )
    )

    cloud_formation_deploy_role = template.add_resource(
        iam.Role(
            "CloudFormationDeployRole",
            RoleName="CloudFormationDeployRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"Service": ["cloudformation.amazonaws.com"]},
                    },
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"AWS": {"Fn::Sub": "${AWS::AccountId}"}},
                    },
                ],
            },
            ManagedPolicyArns=[
                t.Sub("arn:${AWS::Partition}:iam::aws:policy/AdministratorAccess")
            ],
            PermissionsBoundary=t.Ref(
                cloud_formation_deploy_role_permissions_boundary_parameter
            ),
            Path=t.Ref(puppet_role_path_template_parameter),
        )
    )

    pipeline_role = template.add_resource(
        iam.Role(
            "PipelineRole",
            RoleName="PuppetCodePipelineRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"Service": ["codepipeline.amazonaws.com"]},
                    }
                ],
            },
            ManagedPolicyArns=[
                t.Sub("arn:${AWS::Partition}:iam::aws:policy/AdministratorAccess")
            ],
            PermissionsBoundary=t.Ref(
                puppet_code_pipeline_role_permission_boundary_parameter
            ),
            Path=t.Ref(puppet_role_path_template_parameter),
        )
    )

    source_role = template.add_resource(
        iam.Role(
            "SourceRole",
            RoleName="PuppetSourceRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"Service": ["codepipeline.amazonaws.com"]},
                    },
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": {
                                "Fn::Sub": "arn:${AWS::Partition}:iam::${AWS::AccountId}:root"
                            }
                        },
                    },
                ],
            },
            ManagedPolicyArns=[
                t.Sub("arn:${AWS::Partition}:iam::aws:policy/AdministratorAccess")
            ],
            PermissionsBoundary=t.Ref(source_role_permissions_boundary_parameter),
            Path=t.Ref(puppet_role_path_template_parameter),
        )
    )

    dry_run_notification_topic = template.add_resource(
        sns.Topic(
            "DryRunNotificationTopic",
            DisplayName="service-catalog-puppet-dry-run-approvals",
            TopicName="service-catalog-puppet-dry-run-approvals",
            Condition="HasManualApprovals",
        )
    )

    deploy_role = template.add_resource(
        iam.Role(
            "DeployRole",
            RoleName="PuppetDeployRole",
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
            ManagedPolicyArns=[
                t.Sub("arn:${AWS::Partition}:iam::aws:policy/AdministratorAccess")
            ],
            PermissionsBoundary=t.Ref(puppet_deploy_role_permission_boundary_parameter),
            Path=t.Ref(puppet_role_path_template_parameter),
        )
    )

    num_workers_ssm_parameter = template.add_resource(
        ssm.Parameter(
            "NumWorkersSSMParameter",
            Type="String",
            Name="/servicecatalog-puppet/deploy/num-workers",
            Value=t.Sub("${DeployNumWorkers}"),
        )
    )

    parameterised_source_bucket = template.add_resource(
        s3.Bucket(
            "ParameterisedSourceBucket",
            PublicAccessBlockConfiguration=s3.PublicAccessBlockConfiguration(
                IgnorePublicAcls=True,
                BlockPublicPolicy=True,
                BlockPublicAcls=True,
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
            Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
            BucketName=t.Sub("sc-puppet-parameterised-runs-${AWS::AccountId}"),
            VersioningConfiguration=s3.VersioningConfiguration(Status="Enabled"),
        )
    )

    source_stage = codepipeline.Stages(
        Name="Source",
        Actions=[
            codepipeline.Actions(
                RunOrder=1,
                RoleArn=t.GetAtt("SourceRole", "Arn"),
                ActionTypeId=codepipeline.ActionTypeId(
                    Category="Source", Owner="AWS", Version="1", Provider="S3",
                ),
                OutputArtifacts=[
                    codepipeline.OutputArtifacts(Name="ParameterisedSource")
                ],
                Configuration={
                    "S3Bucket": t.Ref(parameterised_source_bucket),
                    "S3ObjectKey": "parameters.zip",
                    "PollForSourceChanges": True,
                },
                Name="ParameterisedSource",
            )
        ],
    )

    install_spec = {
        "runtime-versions": dict(python="3.7"),
        "commands": [
            f"pip install {puppet_version}"
            if "http" in puppet_version
            else f"pip install aws-service-catalog-puppet=={puppet_version}",
        ],
    }

    deploy_env_vars = [
        {
            "Type": "PLAINTEXT",
            "Name": "PUPPET_ACCOUNT_ID",
            "Value": t.Ref("AWS::AccountId"),
        },
        {"Type": "PLAINTEXT", "Name": "PUPPET_REGION", "Value": t.Ref("AWS::Region"),},
        {
            "Type": "PARAMETER_STORE",
            "Name": "PARTITION",
            "Value": t.Ref(partition_parameter),
        },
        {
            "Type": "PARAMETER_STORE",
            "Name": "PUPPET_ROLE_NAME",
            "Value": t.Ref(puppet_role_name_parameter),
        },
        {
            "Type": "PARAMETER_STORE",
            "Name": "PUPPET_ROLE_PATH",
            "Value": t.Ref(puppet_role_path_parameter),
        },
    ]

    if is_codecommit:
        template.add_resource(
            codecommit.Repository(
                "CodeRepo",
                RepositoryName=source.get("Configuration").get("RepositoryName"),
                RepositoryDescription="Repo to store the servicecatalog puppet solution",
                DeletionPolicy="Retain",
            )
        )

        source_stage.Actions.append(
            codepipeline.Actions(
                RunOrder=1,
                RoleArn=t.GetAtt("SourceRole", "Arn"),
                ActionTypeId=codepipeline.ActionTypeId(
                    Category="Source", Owner="AWS", Version="1", Provider="CodeCommit",
                ),
                OutputArtifacts=[codepipeline.OutputArtifacts(Name="Source")],
                Configuration={
                    "RepositoryName": source.get("Configuration").get("RepositoryName"),
                    "BranchName": source.get("Configuration").get("BranchName"),
                    "PollForSourceChanges": source.get("Configuration").get(
                        "PollForSourceChanges", True
                    ),
                },
                Name="Source",
            )
        )

    if is_github:
        source_stage.Actions.append(
            codepipeline.Actions(
                RunOrder=1,
                ActionTypeId=codepipeline.ActionTypeId(
                    Category="Source",
                    Owner="ThirdParty",
                    Version="1",
                    Provider="GitHub",
                ),
                OutputArtifacts=[codepipeline.OutputArtifacts(Name="Source")],
                Configuration={
                    "Owner": source.get("Configuration").get("Owner"),
                    "Repo": source.get("Configuration").get("Repo"),
                    "Branch": source.get("Configuration").get("Branch"),
                    "OAuthToken": t.Join(
                        "",
                        [
                            "{{resolve:secretsmanager:",
                            source.get("Configuration").get("SecretsManagerSecret"),
                            ":SecretString:OAuthToken}}",
                        ],
                    ),
                    "PollForSourceChanges": source.get("Configuration").get(
                        "PollForSourceChanges"
                    ),
                },
                Name="Source",
            )
        )

    if is_custom:
        source_stage.Actions.append(
            codepipeline.Actions(
                RunOrder=1,
                ActionTypeId=codepipeline.ActionTypeId(
                    Category="Source",
                    Owner="Custom",
                    Version=source.get("Configuration").get("CustomActionTypeVersion"),
                    Provider=source.get("Configuration").get(
                        "CustomActionTypeProvider"
                    ),
                ),
                OutputArtifacts=[codepipeline.OutputArtifacts(Name="Source")],
                Configuration={
                    "GitUrl": source.get("Configuration").get("GitUrl"),
                    "Branch": source.get("Configuration").get("Branch"),
                    "PipelineName": t.Sub("${AWS::StackName}-pipeline"),
                },
                Name="Source",
            )
        )
        webhook = codepipeline.Webhook(
            "Webhook",
            Authentication="IP",
            TargetAction="Source",
            AuthenticationConfiguration=codepipeline.WebhookAuthConfiguration(
                AllowedIPRange=source.get("Configuration").get("GitWebHookIpAddress")
            ),
            Filters=[
                codepipeline.WebhookFilterRule(
                    JsonPath="$.changes[0].ref.id", MatchEquals="refs/heads/{Branch}"
                )
            ],
            TargetPipelineVersion=1,
            TargetPipeline=t.Sub("${AWS::StackName}-pipeline"),
        )
        template.add_resource(webhook)
        values_for_sub = {
            "GitUrl": source.get("Configuration").get("GitUrl"),
            "WebhookUrl": t.GetAtt(webhook, "Url"),
        }
        output_to_add = t.Output("WebhookUrl")
        output_to_add.Value = t.Sub("${GitUrl}||${WebhookUrl}", **values_for_sub)
        output_to_add.Export = t.Export(t.Sub("${AWS::StackName}-pipeline"))
        template.add_output(output_to_add)

    if is_codestarsourceconnection:
        source_stage.Actions.append(
            codepipeline.Actions(
                RunOrder=1,
                RoleArn=t.GetAtt("SourceRole", "Arn"),
                ActionTypeId=codepipeline.ActionTypeId(
                    Category="Source",
                    Owner="AWS",
                    Version="1",
                    Provider="CodeStarSourceConnection",
                ),
                OutputArtifacts=[codepipeline.OutputArtifacts(Name="Source")],
                Configuration={
                    "ConnectionArn": source.get("Configuration").get("ConnectionArn"),
                    "FullRepositoryId": source.get("Configuration").get(
                        "FullRepositoryId"
                    ),
                    "BranchName": source.get("Configuration").get("BranchName"),
                    "OutputArtifactFormat": source.get("Configuration").get(
                        "OutputArtifactFormat"
                    ),
                },
                Name="Source",
            )
        )

    if is_s3:
        bucket_name = source.get("Configuration").get("S3Bucket")
        if not scm_skip_creation_of_repo:
            template.add_resource(
                s3.Bucket(
                    bucket_name,
                    PublicAccessBlockConfiguration=s3.PublicAccessBlockConfiguration(
                        IgnorePublicAcls=True,
                        BlockPublicPolicy=True,
                        BlockPublicAcls=True,
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
                    Tags=t.Tags.from_dict(
                        **{"ServiceCatalogPuppet:Actor": "Framework"}
                    ),
                    BucketName=bucket_name,
                    VersioningConfiguration=s3.VersioningConfiguration(
                        Status="Enabled"
                    ),
                )
            )

        source_stage.Actions.append(
            codepipeline.Actions(
                RunOrder=1,
                ActionTypeId=codepipeline.ActionTypeId(
                    Category="Source", Owner="AWS", Version="1", Provider="S3",
                ),
                OutputArtifacts=[codepipeline.OutputArtifacts(Name="Source")],
                Configuration={
                    "S3Bucket": bucket_name,
                    "S3ObjectKey": source.get("Configuration").get("S3ObjectKey"),
                    "PollForSourceChanges": source.get("Configuration").get(
                        "PollForSourceChanges"
                    ),
                },
                Name="Source",
            )
        )

    single_account_run_project_build_spec = dict(
        version=0.2,
        phases=dict(
            install=install_spec,
            build={
                "commands": [
                    'echo "single_account: \\"${SINGLE_ACCOUNT_ID}\\"" > parameters.yaml',
                    "cat parameters.yaml",
                    "zip parameters.zip parameters.yaml",
                    "aws s3 cp parameters.zip s3://sc-puppet-parameterised-runs-${PUPPET_ACCOUNT_ID}/parameters.zip",
                ]
            },
            post_build={
                "commands": [
                    "servicecatalog-puppet wait-for-parameterised-run-to-complete",
                ]
            },
        ),
        artifacts=dict(
            name="DeployProject",
            files=[
                "ServiceCatalogPuppet/manifest.yaml",
                "ServiceCatalogPuppet/manifest-expanded.yaml",
                "results/*/*",
                "output/*/*",
                "exploded_results/*/*",
                "tasks.log",
            ],
        ),
    )

    single_account_run_project_args = dict(
        Name="servicecatalog-puppet-single-account-run",
        Description="Runs puppet for a single account - SINGLE_ACCOUNT_ID",
        ServiceRole=t.GetAtt(deploy_role, "Arn"),
        Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
        Artifacts=codebuild.Artifacts(Type="NO_ARTIFACTS",),
        TimeoutInMinutes=480,
        Environment=codebuild.Environment(
            ComputeType=t.Ref(deploy_environment_compute_type_parameter),
            Image="aws/codebuild/standard:4.0",
            Type="LINUX_CONTAINER",
            EnvironmentVariables=[
                {
                    "Type": "PLAINTEXT",
                    "Name": "SINGLE_ACCOUNT_ID",
                    "Value": "CHANGE_ME",
                },
            ]
            + deploy_env_vars,
        ),
        Source=codebuild.Source(
            Type="NO_SOURCE",
            BuildSpec=yaml.safe_dump(single_account_run_project_build_spec),
        ),
    )

    single_account_run_project = template.add_resource(
        codebuild.Project("SingleAccountRunProject", **single_account_run_project_args)
    )

    single_account_run_project_build_spec["phases"]["post_build"]["commands"] = [
        "servicecatalog-puppet wait-for-parameterised-run-to-complete --on-complete-url $CALLBACK_URL"
    ]
    single_account_run_project_args[
        "Name"
    ] = "servicecatalog-puppet-single-account-run-with-callback"
    single_account_run_project_args[
        "Description"
    ] = "Runs puppet for a single account - SINGLE_ACCOUNT_ID and then does a http put"
    single_account_run_project_args.get("Environment").EnvironmentVariables.append(
        {"Type": "PLAINTEXT", "Name": "CALLBACK_URL", "Value": "CHANGE_ME",}
    )
    single_account_run_project_args["Source"] = codebuild.Source(
        Type="NO_SOURCE",
        BuildSpec=yaml.safe_dump(single_account_run_project_build_spec),
    )
    single_account_run_project_with_callback = template.add_resource(
        codebuild.Project(
            "SingleAccountRunWithCallbackProject", **single_account_run_project_args
        )
    )

    stages = [source_stage]

    if should_validate:
        template.add_resource(
            codebuild.Project(
                "ValidateProject",
                Name="servicecatalog-puppet-validate",
                ServiceRole=t.GetAtt("DeployRole", "Arn"),
                Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
                Artifacts=codebuild.Artifacts(Type="CODEPIPELINE"),
                TimeoutInMinutes=60,
                Environment=codebuild.Environment(
                    ComputeType="BUILD_GENERAL1_SMALL",
                    Image="aws/codebuild/standard:4.0",
                    Type="LINUX_CONTAINER",
                ),
                Source=codebuild.Source(
                    BuildSpec=yaml.safe_dump(
                        dict(
                            version="0.2",
                            phases={
                                "install": {
                                    "runtime-versions": {"python": "3.7",},
                                    "commands": [
                                        f"pip install {puppet_version}"
                                        if "http" in puppet_version
                                        else f"pip install aws-service-catalog-puppet=={puppet_version}",
                                    ],
                                },
                                "build": {
                                    "commands": [
                                        "servicecatalog-puppet validate manifest.yaml"
                                    ]
                                },
                            },
                        )
                    ),
                    Type="CODEPIPELINE",
                ),
                Description="Validate the manifest.yaml file",
            )
        )
        stages.append(
            codepipeline.Stages(
                Name="Validate",
                Actions=[
                    codepipeline.Actions(
                        InputArtifacts=[codepipeline.InputArtifacts(Name="Source"),],
                        Name="Validate",
                        ActionTypeId=codepipeline.ActionTypeId(
                            Category="Build",
                            Owner="AWS",
                            Version="1",
                            Provider="CodeBuild",
                        ),
                        OutputArtifacts=[
                            codepipeline.OutputArtifacts(Name="ValidateProject")
                        ],
                        Configuration={
                            "ProjectName": t.Ref("ValidateProject"),
                            "PrimarySource": "Source",
                        },
                        RunOrder=1,
                    ),
                ],
            )
        )

    if is_manual_approvals:
        deploy_stage = codepipeline.Stages(
            Name="Deploy",
            Actions=[
                codepipeline.Actions(
                    InputArtifacts=[
                        codepipeline.InputArtifacts(Name="Source"),
                        codepipeline.InputArtifacts(Name="ParameterisedSource"),
                    ],
                    Name="DryRun",
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category="Build",
                        Owner="AWS",
                        Version="1",
                        Provider="CodeBuild",
                    ),
                    OutputArtifacts=[
                        codepipeline.OutputArtifacts(Name="DryRunProject")
                    ],
                    Configuration={
                        "ProjectName": t.Ref("DryRunProject"),
                        "PrimarySource": "Source",
                    },
                    RunOrder=1,
                ),
                codepipeline.Actions(
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category="Approval",
                        Owner="AWS",
                        Version="1",
                        Provider="Manual",
                    ),
                    Configuration={
                        "NotificationArn": t.Ref("DryRunNotificationTopic"),
                        "CustomData": "Approve when you are happy with the dry run.",
                    },
                    Name="DryRunApproval",
                    RunOrder=2,
                ),
                codepipeline.Actions(
                    InputArtifacts=[
                        codepipeline.InputArtifacts(Name="Source"),
                        codepipeline.InputArtifacts(Name="ParameterisedSource"),
                    ],
                    Name="Deploy",
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category="Build",
                        Owner="AWS",
                        Version="1",
                        Provider="CodeBuild",
                    ),
                    OutputArtifacts=[
                        codepipeline.OutputArtifacts(Name="DeployProject")
                    ],
                    Configuration={
                        "ProjectName": t.Ref("DeployProject"),
                        "PrimarySource": "Source",
                    },
                    RunOrder=3,
                ),
            ],
        )
    else:
        deploy_stage = codepipeline.Stages(
            Name="Deploy",
            Actions=[
                codepipeline.Actions(
                    InputArtifacts=[
                        codepipeline.InputArtifacts(Name="Source"),
                        codepipeline.InputArtifacts(Name="ParameterisedSource"),
                    ],
                    Name="Deploy",
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category="Build",
                        Owner="AWS",
                        Version="1",
                        Provider="CodeBuild",
                    ),
                    OutputArtifacts=[
                        codepipeline.OutputArtifacts(Name="DeployProject")
                    ],
                    Configuration={
                        "ProjectName": t.Ref("DeployProject"),
                        "PrimarySource": "Source",
                        "EnvironmentVariables": '[{"name":"EXECUTION_ID","value":"#{codepipeline.PipelineExecutionId}","type":"PLAINTEXT"}]',
                    },
                    RunOrder=1,
                ),
            ],
        )

    stages.append(deploy_stage)

    pipeline = template.add_resource(
        codepipeline.Pipeline(
            "Pipeline",
            RoleArn=t.GetAtt("PipelineRole", "Arn"),
            Stages=stages,
            Name=t.Sub("${AWS::StackName}-pipeline"),
            ArtifactStore=codepipeline.ArtifactStore(
                Type="S3",
                Location=t.Sub(
                    "sc-puppet-pipeline-artifacts-${AWS::AccountId}-${AWS::Region}"
                ),
            ),
            RestartExecutionOnUpdate=True,
        )
    )

    if is_github:
        template.add_resource(
            codepipeline.Webhook(
                "Webhook",
                AuthenticationConfiguration=codepipeline.WebhookAuthConfiguration(
                    SecretToken=t.Join(
                        "",
                        [
                            "{{resolve:secretsmanager:",
                            source.get("Configuration").get("SecretsManagerSecret"),
                            ":SecretString:SecretToken}}",
                        ],
                    )
                ),
                Filters=[
                    codepipeline.WebhookFilterRule(
                        JsonPath="$.ref",
                        MatchEquals="refs/heads/"
                        + source.get("Configuration").get("Branch"),
                    )
                ],
                Authentication="GITHUB_HMAC",
                TargetPipeline=t.Ref(pipeline),
                TargetAction="Source",
                Name=t.Sub("${AWS::StackName}-webhook"),
                TargetPipelineVersion=t.GetAtt(pipeline, "Version"),
                RegisterWithThirdParty="true",
            )
        )

    deploy_project_build_spec = dict(
        version=0.2,
        phases=dict(
            install={
                "runtime-versions": dict(python="3.7"),
                "commands": [
                    f"pip install {puppet_version}"
                    if "http" in puppet_version
                    else f"pip install aws-service-catalog-puppet=={puppet_version}",
                ],
            },
            pre_build={
                "commands": [
                    "servicecatalog-puppet --info expand --parameter-override-file $CODEBUILD_SRC_DIR_ParameterisedSource/parameters.yaml manifest.yaml",
                ]
            },
            build={
                "commands": [
                    "servicecatalog-puppet --info deploy --num-workers ${NUM_WORKERS} manifest-expanded.yaml",
                ]
            },
        ),
        artifacts=dict(
            name="DeployProject",
            files=[
                "manifest-expanded.yaml",
                "results/*/*",
                "output/*/*",
                "exploded_results/*/*",
                "tasks.log",
            ],
        ),
    )

    deploy_project_args = dict(
        Name="servicecatalog-puppet-deploy",
        ServiceRole=t.GetAtt(deploy_role, "Arn"),
        Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
        Artifacts=codebuild.Artifacts(Type="CODEPIPELINE",),
        TimeoutInMinutes=480,
        Environment=codebuild.Environment(
            ComputeType=t.Ref(deploy_environment_compute_type_parameter),
            Image="aws/codebuild/standard:4.0",
            Type="LINUX_CONTAINER",
            EnvironmentVariables=[
                {
                    "Type": "PARAMETER_STORE",
                    "Name": "NUM_WORKERS",
                    "Value": t.Ref(num_workers_ssm_parameter),
                },
                {
                    "Type": "PARAMETER_STORE",
                    "Name": "SPOKE_EXECUTION_MODE_DEPLOY_ENV",
                    "Value": constants.SPOKE_EXECUTION_MODE_DEPLOY_ENV_PARAMETER_NAME,
                },
            ]
            + deploy_env_vars,
        ),
        Source=codebuild.Source(
            Type="CODEPIPELINE", BuildSpec=yaml.safe_dump(deploy_project_build_spec),
        ),
        Description="deploys out the products to be deployed",
    )

    deploy_project = template.add_resource(
        codebuild.Project("DeployProject", **deploy_project_args)
    )

    deploy_project_build_spec["phases"]["build"]["commands"] = [
        "servicecatalog-puppet --info dry-run manifest-expanded.yaml"
    ]
    deploy_project_build_spec["artifacts"]["name"] = "DryRunProject"
    deploy_project_args["Name"] = "servicecatalog-puppet-dryrun"
    deploy_project_args["Description"] = "dry run of servicecatalog-puppet-dryrun"
    deploy_project_args["Source"] = codebuild.Source(
        Type="CODEPIPELINE", BuildSpec=yaml.safe_dump(deploy_project_build_spec),
    )

    dry_run_project = template.add_resource(
        codebuild.Project("DryRunProject", **deploy_project_args)
    )

    bootstrap_project = template.add_resource(
        codebuild.Project(
            "BootstrapProject",
            Name="servicecatalog-puppet-bootstrap-spokes-in-ou",
            ServiceRole=t.GetAtt("DeployRole", "Arn"),
            Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
            Artifacts=codebuild.Artifacts(Type="NO_ARTIFACTS"),
            TimeoutInMinutes=60,
            Environment=codebuild.Environment(
                ComputeType="BUILD_GENERAL1_SMALL",
                Image="aws/codebuild/standard:4.0",
                Type="LINUX_CONTAINER",
                EnvironmentVariables=[
                    {"Type": "PLAINTEXT", "Name": "OU_OR_PATH", "Value": "CHANGE_ME"},
                    {
                        "Type": "PLAINTEXT",
                        "Name": "IAM_ROLE_NAME",
                        "Value": "OrganizationAccountAccessRole",
                    },
                    {"Type": "PLAINTEXT", "Name": "IAM_ROLE_ARNS", "Value": ""},
                    {"Type": "PLAINTEXT", "Name": "OPTIONS", "Value": ""},
                ],
            ),
            Source=codebuild.Source(
                BuildSpec="version: 0.2\nphases:\n  install:\n    runtime-versions:\n      python: 3.7\n    commands:\n      - pip install aws-service-catalog-puppet\n  build:\n    commands:\n      - servicecatalog-puppet bootstrap-spokes-in-ou $OU_OR_PATH $IAM_ROLE_NAME $IAM_ROLE_ARNS ${OPTIONS}\nartifacts:\n  files:\n    - results/*/*\n    - output/*/*\n  name: BootstrapProject\n",
                Type="NO_SOURCE",
            ),
            Description="Bootstrap all the accounts in an OU",
        )
    )

    template.add_resource(
        codebuild.Project(
            "BootstrapASpokeProject",
            Name="servicecatalog-puppet-bootstrap-spoke",
            ServiceRole=t.GetAtt("DeployRole", "Arn"),
            Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
            Artifacts=codebuild.Artifacts(Type="NO_ARTIFACTS"),
            TimeoutInMinutes=60,
            Environment=codebuild.Environment(
                ComputeType="BUILD_GENERAL1_SMALL",
                Image="aws/codebuild/standard:4.0",
                Type="LINUX_CONTAINER",
                EnvironmentVariables=[
                    {
                        "Type": "PLAINTEXT",
                        "Name": "PUPPET_ACCOUNT_ID",
                        "Value": t.Sub("${AWS::AccountId}"),
                    },
                    {
                        "Type": "PLAINTEXT",
                        "Name": "ORGANIZATION_ACCOUNT_ACCESS_ROLE_ARN",
                        "Value": "CHANGE_ME",
                    },
                    {
                        "Type": "PLAINTEXT",
                        "Name": "ASSUMABLE_ROLE_IN_ROOT_ACCOUNT",
                        "Value": "CHANGE_ME",
                    },
                    {"Type": "PLAINTEXT", "Name": "OPTIONS", "Value": "CHANGE_ME",},
                ],
            ),
            Source=codebuild.Source(
                BuildSpec=yaml.safe_dump(
                    dict(
                        version=0.2,
                        phases=dict(
                            install=install_spec,
                            build={
                                "commands": [
                                    "servicecatalog-puppet bootstrap-spoke-as ${PUPPET_ACCOUNT_ID} ${ASSUMABLE_ROLE_IN_ROOT_ACCOUNT} ${ORGANIZATION_ACCOUNT_ACCESS_ROLE_ARN} ${OPTIONS}"
                                ]
                            },
                        ),
                    )
                ),
                Type="NO_SOURCE",
            ),
            Description="Bootstrap given account as a spoke",
        )
    )

    cloud_formation_events_queue = template.add_resource(
        sqs.Queue(
            "CloudFormationEventsQueue",
            QueueName="servicecatalog-puppet-cloudformation-events",
            Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
        )
    )

    cloud_formation_events_queue_policy = template.add_resource(
        sqs.QueuePolicy(
            "CloudFormationEventsQueuePolicy",
            Queues=[t.Ref(cloud_formation_events_queue)],
            PolicyDocument={
                "Id": "AllowSNS",
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "allow-send-message",
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["sqs:SendMessage"],
                        "Resource": "*",
                        "Condition": {
                            "ArnEquals": {
                                "aws:SourceArn": t.Sub(
                                    "arn:${AWS::Partition}:sns:*:${AWS::AccountId}:servicecatalog-puppet-cloudformation-regional-events"
                                )
                            }
                        },
                    }
                ],
            },
        )
    )

    spoke_deploy_bucket = template.add_resource(
        s3.Bucket(
            "SpokeDeployBucket",
            PublicAccessBlockConfiguration=s3.PublicAccessBlockConfiguration(
                IgnorePublicAcls=True,
                BlockPublicPolicy=True,
                BlockPublicAcls=True,
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
            Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
            BucketName=t.Sub("sc-puppet-spoke-deploy-${AWS::AccountId}"),
            VersioningConfiguration=s3.VersioningConfiguration(Status="Enabled"),
        )
    )

    caching_bucket = template.add_resource(
        s3.Bucket(
            "CachingBucket",
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
            Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
            BucketName=t.Sub(
                "sc-puppet-caching-bucket-${AWS::AccountId}-${AWS::Region}"
            ),
            VersioningConfiguration=s3.VersioningConfiguration(Status="Enabled"),
        )
    )

    template.add_output(
        t.Output(
            "CloudFormationEventsQueueArn",
            Value=t.GetAtt(cloud_formation_events_queue, "Arn"),
        )
    )
    template.add_output(t.Output("Version", Value=t.GetAtt(param, "Value")))
    template.add_output(
        t.Output(
            "ManualApprovalsParam", Value=t.GetAtt(manual_approvals_param, "Value")
        )
    )

    template.add_resource(
        ssm.Parameter(
            "DefaultTerraformVersion",
            Type="String",
            Name=constants.DEFAULT_TERRAFORM_VERSION_PARAMETER_NAME,
            Value=constants.DEFAULT_TERRAFORM_VERSION_VALUE,
        )
    )

    return template
