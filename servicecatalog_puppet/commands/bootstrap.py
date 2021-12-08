#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import io
import os
import zipfile
from threading import Thread

import botocore
import click
from betterboto import client as betterboto_client

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.template_builder.hub import (
    bootstrap_region as hub_bootstrap_region,
    bootstrap as hub_bootstrap,
)


def bootstrap(
    puppet_account_id,
    with_manual_approvals,
    puppet_code_pipeline_role_permission_boundary,
    source_role_permissions_boundary,
    puppet_generate_role_permission_boundary,
    puppet_deploy_role_permission_boundary,
    puppet_provisioning_role_permissions_boundary,
    cloud_formation_deploy_role_permissions_boundary,
    deploy_environment_compute_type,
    spoke_deploy_environment_compute_type,
    deploy_num_workers,
    source_provider,
    owner,
    repo,
    branch,
    poll_for_source_changes,
    webhook_secret,
    puppet_role_name,
    puppet_role_path,
    scm_connection_arn,
    scm_full_repository_id,
    scm_branch_name,
    scm_bucket_name,
    scm_object_key,
    scm_skip_creation_of_repo,
    should_validate,
    custom_source_action_git_url,
    custom_source_action_git_web_hook_ip_address,
    custom_source_action_custom_action_type_version,
    custom_source_action_custom_action_type_provider,
):
    click.echo("Starting bootstrap")
    should_use_eventbridge = config.get_should_use_eventbridge(
        puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
    )
    initialiser_stack_tags = config.get_initialiser_stack_tags()
    if should_use_eventbridge:
        with betterboto_client.ClientContextManager("events") as events:
            try:
                events.describe_event_bus(Name=constants.EVENT_BUS_NAME)
            except events.exceptions.ResourceNotFoundException:
                events.create_event_bus(Name=constants.EVENT_BUS_NAME,)

    all_regions = config.get_regions(
        puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
    )
    with betterboto_client.MultiRegionClientContextManager(
        "cloudformation", all_regions
    ) as clients:
        click.echo("Creating {}-regional".format(constants.BOOTSTRAP_STACK_NAME))
        threads = []
        template = hub_bootstrap_region.get_template(
            constants.VERSION, os.environ.get("AWS_DEFAULT_REGION")
        ).to_yaml(clean_up=True)
        args = {
            "StackName": "{}-regional".format(constants.BOOTSTRAP_STACK_NAME),
            "TemplateBody": template,
            "Capabilities": ["CAPABILITY_IAM"],
            "Parameters": [
                {
                    "ParameterKey": "Version",
                    "ParameterValue": constants.VERSION,
                    "UsePreviousValue": False,
                },
                {
                    "ParameterKey": "DefaultRegionValue",
                    "ParameterValue": os.environ.get("AWS_DEFAULT_REGION"),
                    "UsePreviousValue": False,
                },
            ],
            "Tags": [{"Key": "ServiceCatalogPuppet:Actor", "Value": "Framework",}]
            + initialiser_stack_tags,
        }
        for client_region, client in clients.items():
            process = Thread(
                name=client_region, target=client.create_or_update, kwargs=args
            )
            process.start()
            threads.append(process)
        for process in threads:
            process.join()
        click.echo(
            "Finished creating {}-regional".format(constants.BOOTSTRAP_STACK_NAME)
        )

    source_args = {"Provider": source_provider}
    if source_provider == "CodeCommit":
        source_args.update(
            {
                "Configuration": {
                    "RepositoryName": repo,
                    "BranchName": branch,
                    "PollForSourceChanges": poll_for_source_changes,
                },
            }
        )
    elif source_provider == "GitHub":
        source_args.update(
            {
                "Configuration": {
                    "Owner": owner,
                    "Repo": repo,
                    "Branch": branch,
                    "PollForSourceChanges": poll_for_source_changes,
                    "SecretsManagerSecret": webhook_secret,
                },
            }
        )
    elif source_provider.lower() == "codestarsourceconnection":
        source_args.update(
            {
                "Configuration": {
                    "ConnectionArn": scm_connection_arn,
                    "FullRepositoryId": scm_full_repository_id,
                    "BranchName": scm_branch_name,
                    "OutputArtifactFormat": "CODE_ZIP",
                    "DetectChanges": poll_for_source_changes,
                },
            }
        )
    elif source_provider.lower() == "s3":
        source_args.update(
            {
                "Configuration": {
                    "S3Bucket": scm_bucket_name,
                    "S3ObjectKey": scm_object_key,
                    "PollForSourceChanges": poll_for_source_changes,
                },
            }
        )
    elif source_provider.lower() == "custom":
        source_args.update(
            {
                "Configuration": {
                    "Owner": "Custom",
                    "GitUrl": custom_source_action_git_url,
                    "Branch": branch,
                    "GitWebHookIpAddress": custom_source_action_git_web_hook_ip_address,
                    "CustomActionTypeVersion": custom_source_action_custom_action_type_version,
                    "CustomActionTypeProvider": custom_source_action_custom_action_type_provider,
                },
            }
        )

    template = hub_bootstrap.get_template(
        constants.VERSION,
        all_regions,
        source_args,
        config.is_caching_enabled(
            puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
        ),
        with_manual_approvals,
        scm_skip_creation_of_repo,
        should_validate,
    ).to_yaml(clean_up=True)

    args = {
        "StackName": constants.BOOTSTRAP_STACK_NAME,
        "TemplateBody": template,
        "Capabilities": ["CAPABILITY_NAMED_IAM"],
        "Parameters": [
            {
                "ParameterKey": "Version",
                "ParameterValue": constants.VERSION,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "OrgIamRoleArn",
                "ParameterValue": str(config.get_org_iam_role_arn(puppet_account_id)),
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "WithManualApprovals",
                "ParameterValue": "Yes" if with_manual_approvals else "No",
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetCodePipelineRolePermissionBoundary",
                "ParameterValue": puppet_code_pipeline_role_permission_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "SourceRolePermissionsBoundary",
                "ParameterValue": source_role_permissions_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetGenerateRolePermissionBoundary",
                "ParameterValue": puppet_generate_role_permission_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetDeployRolePermissionBoundary",
                "ParameterValue": puppet_deploy_role_permission_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetProvisioningRolePermissionsBoundary",
                "ParameterValue": puppet_provisioning_role_permissions_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "CloudFormationDeployRolePermissionsBoundary",
                "ParameterValue": cloud_formation_deploy_role_permissions_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "DeployEnvironmentComputeType",
                "ParameterValue": deploy_environment_compute_type,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "SpokeDeployEnvironmentComputeType",
                "ParameterValue": spoke_deploy_environment_compute_type,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "DeployNumWorkers",
                "ParameterValue": str(deploy_num_workers),
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetRoleName",
                "ParameterValue": puppet_role_name,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetRolePath",
                "ParameterValue": puppet_role_path,
                "UsePreviousValue": False,
            },
        ],
        "Tags": [{"Key": "ServiceCatalogPuppet:Actor", "Value": "Framework",}]
        + initialiser_stack_tags,
    }
    with betterboto_client.ClientContextManager("cloudformation") as cloudformation:
        click.echo("Creating {}".format(constants.BOOTSTRAP_STACK_NAME))
        cloudformation.create_or_update(**args)

    buff = io.BytesIO()
    with zipfile.ZipFile(buff, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("parameters.yaml", 'single_account: "000000000000"')

    with betterboto_client.ClientContextManager("s3") as s3:
        try:
            s3.head_object(
                Bucket=f"sc-puppet-parameterised-runs-{puppet_account_id}",
                Key="parameters.zip",
            )
        except botocore.exceptions.ClientError as ex:
            if ex.response["Error"]["Code"] == "404":
                s3.put_object(
                    Bucket=f"sc-puppet-parameterised-runs-{puppet_account_id}",
                    Key="parameters.zip",
                    Body=buff.getvalue(),
                )

    click.echo("Finished creating {}.".format(constants.BOOTSTRAP_STACK_NAME))
