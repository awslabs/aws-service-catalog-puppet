#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import copy

import luigi
import troposphere as t
import yaml
from troposphere import s3, codebuild

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks


class CreateTemplateForWorkspaceTask(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        puppet_version = constants.VERSION
        description = f"""Bootstrap template used to configure spoke account for terraform use
        {{"version": "{puppet_version}", "framework": "servicecatalog-puppet", "role": "bootstrap-spoke-terraform"}}"""

        service_role = t.Sub(
            "arn:aws:iam::${AWS::AccountId}:role/servicecatalog-puppet/PuppetDeployInSpokeRole"
        )
        template = t.Template(Description=description)
        state = template.add_resource(
            s3.Bucket(
                "state",
                BucketName=t.Sub("sc-puppet-state-${AWS::AccountId}"),
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
        template.add_resource(
            s3.BucketPolicy(
                "statePolicy",
                Bucket=t.Ref(state),
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["s3:GetObject*", "s3:PutObject*",],
                            "Principal": {"AWS": self.puppet_account_id},
                            "Resource": t.Join("/", [t.GetAtt(state, "Arn"), "*"]),
                            "Effect": "Allow",
                            "Sid": "AllowPuppet",
                        },
                    ],
                },
            )
        )
        execute_build_spec = dict(
            version="0.2",
            phases=dict(
                install=dict(
                    commands=[
                        "mkdir -p /root/downloads",
                        "curl -s -qL -o /root/downloads/terraform_${TERRAFORM_VERSION}_linux_amd64.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip",
                        "unzip /root/downloads/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/bin/",
                        "chmod +x /usr/bin/terraform",
                        "terraform --version",
                        "aws s3 cp $ZIP source.zip",
                        "unzip source.zip",
                    ],
                ),
                pre_build=dict(
                    commands=[
                        "aws s3 cp $STATE_FILE terraform.tfstate || echo 'no statefile copied'",
                        'ASSUME_ROLE_ARN="arn:aws:iam::${TARGET_ACCOUNT}:role/servicecatalog-puppet/PuppetRole"',
                        "TEMP_ROLE=$(aws sts assume-role --role-arn $ASSUME_ROLE_ARN --role-session-name terraform)",
                        "export TEMP_ROLE",
                        'export AWS_ACCESS_KEY_ID=$(echo "${TEMP_ROLE}" | jq -r ".Credentials.AccessKeyId")',
                        'export AWS_SECRET_ACCESS_KEY=$(echo "${TEMP_ROLE}" | jq -r ".Credentials.SecretAccessKey")',
                        'export AWS_SESSION_TOKEN=$(echo "${TEMP_ROLE}" | jq -r ".Credentials.SessionToken")',
                        "aws sts get-caller-identity",
                        "terraform init",
                    ],
                ),
                build=dict(commands=["terraform apply -auto-approve",]),
                post_build=dict(
                    commands=[
                        "terraform output -json > outputs.json",
                        "unset AWS_ACCESS_KEY_ID",
                        "unset AWS_SECRET_ACCESS_KEY",
                        "unset AWS_SESSION_TOKEN",
                        "aws sts get-caller-identity",
                        "aws s3 cp terraform.tfstate $STATE_FILE",
                    ]
                ),
            ),
            artifacts=dict(files=["outputs.json",],),
        )
        execute_terraform = dict(
            Name=constants.EXECUTE_TERRAFORM_PROJECT_NAME,
            ServiceRole=service_role,
            Tags=t.Tags.from_dict(**{"ServiceCatalogPuppet:Actor": "Framework"}),
            Artifacts=codebuild.Artifacts(
                Type="S3",
                Location=t.Ref("state"),
                Path="terraform-executions",
                Name="artifacts-execute",
                NamespaceType="BUILD_ID",
            ),
            TimeoutInMinutes=480,
            Environment=codebuild.Environment(
                ComputeType="BUILD_GENERAL1_SMALL",
                Image=constants.CODEBUILD_DEFAULT_IMAGE,
                Type="LINUX_CONTAINER",
                EnvironmentVariables=[
                    codebuild.EnvironmentVariable(
                        Name="TERRAFORM_VERSION",
                        Type="PARAMETER_STORE",
                        Value=constants.DEFAULT_TERRAFORM_VERSION_PARAMETER_NAME,
                    ),
                ]
                + [
                    codebuild.EnvironmentVariable(
                        Name=name, Type="PLAINTEXT", Value="CHANGE_ME",
                    )
                    for name in ["TARGET_ACCOUNT", "ZIP", "STATE_FILE"]
                ],
            ),
            Source=codebuild.Source(
                BuildSpec=yaml.safe_dump(execute_build_spec), Type="NO_SOURCE",
            ),
            Description="Execute the given terraform in the given account using the given state file",
        )

        # execute
        template.add_resource(
            codebuild.Project("ExecuteTerraformProject", **execute_terraform)
        )

        # execute dry run
        execute_dry_run_terraform = copy.deepcopy(execute_terraform)
        execute_dry_run_terraform[
            "Name"
        ] = constants.EXECUTE_DRY_RUN_TERRAFORM_PROJECT_NAME
        execute_dry_run_terraform["Description"] = execute_dry_run_terraform[
            "Description"
        ].replace("Execute", "DRY RUN of Execute")
        execute_dry_run_build_spec = copy.deepcopy(execute_build_spec)
        execute_dry_run_build_spec["phases"]["build"]["commands"] = [
            "terraform plan -out=plan.bin",
            "terraform show -json plan.bin > plan.json",
        ]
        del execute_dry_run_build_spec["phases"]["post_build"]
        execute_dry_run_build_spec["artifacts"] = dict(
            files=["plan.bin", "plan.json",],
        )
        execute_dry_run_terraform["Source"] = codebuild.Source(
            BuildSpec=yaml.safe_dump(execute_dry_run_build_spec), Type="NO_SOURCE",
        )
        execute_dry_run_terraform["Artifacts"] = codebuild.Artifacts(
            Type="S3",
            Location=t.Ref("state"),
            Path="terraform-executions",
            Name="artifacts-execute-dry-run",
            NamespaceType="BUILD_ID",
        )
        template.add_resource(
            codebuild.Project(
                "ExecuteDryRunTerraformProject", **execute_dry_run_terraform
            )
        )

        # terminate
        terminate_terraform = copy.deepcopy(execute_terraform)
        terminate_terraform["Name"] = constants.TERMINATE_TERRAFORM_PROJECT_NAME
        terminate_terraform["Description"] = terminate_terraform["Description"].replace(
            "Execute", "Terminate"
        )
        terminate_build_spec = copy.deepcopy(execute_build_spec)
        terminate_build_spec["phases"]["build"]["commands"] = [
            "terraform destroy -auto-approve"
        ]
        terminate_build_spec["phases"]["post_build"]["commands"] = [
            "unset AWS_ACCESS_KEY_ID",
            "unset AWS_SECRET_ACCESS_KEY",
            "unset AWS_SESSION_TOKEN",
            "aws sts get-caller-identity",
            "aws s3 cp terraform.tfstate $STATE_FILE",
        ]
        del terminate_build_spec["artifacts"]
        terminate_terraform["Source"] = codebuild.Source(
            BuildSpec=yaml.safe_dump(terminate_build_spec), Type="NO_SOURCE",
        )
        terminate_terraform["Artifacts"] = codebuild.Artifacts(
            Type="S3",
            Location=t.Ref("state"),
            Path="terraform-executions",
            Name="artifacts-terminate",
            NamespaceType="BUILD_ID",
        )
        template.add_resource(
            codebuild.Project("TerminateTerraformProject", **terminate_terraform)
        )

        # terminate dry run
        termminate_dry_run_terraform = copy.deepcopy(execute_terraform)
        termminate_dry_run_terraform[
            "Name"
        ] = constants.TERMINATE_DRY_RUN_TERRAFORM_PROJECT_NAME
        new_description = termminate_dry_run_terraform["Description"].replace(
            "Execute", "DRY RUN of Terminate"
        )
        termminate_dry_run_terraform["Description"] = new_description
        termminate_dry_run_build_spec = copy.deepcopy(execute_build_spec)
        termminate_dry_run_build_spec["phases"]["build"]["commands"] = [
            "terraform plan -destroy -out=plan.bin",
            "terraform show -json plan.bin > plan.json",
        ]
        del termminate_dry_run_build_spec["phases"]["post_build"]
        termminate_dry_run_build_spec["artifacts"] = dict(
            files=["plan.bin", "plan.json",],
        )
        termminate_dry_run_terraform["Source"] = codebuild.Source(
            BuildSpec=yaml.safe_dump(termminate_dry_run_build_spec), Type="NO_SOURCE",
        )
        termminate_dry_run_terraform["Artifacts"] = codebuild.Artifacts(
            Type="S3",
            Location=t.Ref("state"),
            Path="terraform-executions",
            Name="artifacts-terminate-dry-run",
            NamespaceType="BUILD_ID",
        )
        template.add_resource(
            codebuild.Project(
                "TerminateDryRunTerraformProject", **termminate_dry_run_terraform
            )
        )

        self.write_output(template.to_yaml(), skip_json_dump=True)
