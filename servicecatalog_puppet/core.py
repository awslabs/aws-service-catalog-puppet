# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import cfn_tools
import requests
import terminaltables

import shutil
from threading import Thread

import pkg_resources
import yaml
import logging
import os
import click
from datetime import datetime

from jinja2 import Template
from pykwalify.core import Core
from betterboto import client as betterboto_client

from servicecatalog_puppet import manifest_utils_for_launches
from servicecatalog_puppet.workflow import management as management_tasks
from servicecatalog_puppet.workflow import provisioning as provisioning_tasks
from servicecatalog_puppet.workflow import runner as runner
from servicecatalog_puppet.workflow import launch as launch_tasks
from servicecatalog_puppet.workflow import (
    lambda_invocations as lambda_invocations_tasks,
)
from servicecatalog_puppet.workflow import (
    spoke_local_portfolios as spoke_local_portfolios_tasks,
)
from servicecatalog_puppet import config
from servicecatalog_puppet import manifest_utils
from servicecatalog_puppet import aws

from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import constants

import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def cli(info, info_line_numbers):
    if info:
        logging.basicConfig(
            format="%(levelname)s %(threadName)s %(message)s", level=logging.INFO
        )
    if info_line_numbers:
        logging.basicConfig(
            format="%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d:%H:%M:%S",
            level=logging.INFO,
        )


def reset_provisioned_product_owner(f):
    puppet_account_id = config.get_puppet_account_id()
    current_account_id = puppet_account_id
    manifest = manifest_utils.load(f, puppet_account_id)

    task_defs = manifest_utils_for_launches.generate_launch_tasks(
        manifest, puppet_account_id, False, False
    )

    tasks_to_run = []
    for task in task_defs:
        task_status = task.get("status")
        if task_status == constants.PROVISIONED:
            tasks_to_run.append(
                provisioning_tasks.ResetProvisionedProductOwnerTask(
                    launch_name=task.get("launch_name"),
                    account_id=task.get("account_id"),
                    region=task.get("region"),
                )
            )

    cache_invalidator = str(datetime.now())

    runner.run_tasks(
        puppet_account_id,
        current_account_id,
        tasks_to_run,
        10,
        cache_invalidator=cache_invalidator,
        on_complete_url=None,
    )


def generate_tasks(
    f,
    puppet_account_id,
    executor_account_id,
    single_account=None,
    is_dry_run=False,
    execution_mode="hub",
    cache_invalidator="now",
):
    should_use_sns = config.get_should_use_sns(
        puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
    )
    should_use_product_plans = config.get_should_use_product_plans(
        puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
    )

    return [
        launch_tasks.LaunchSectionTask(
            manifest_file_path=f.name,
            puppet_account_id=puppet_account_id,
            should_use_sns=should_use_sns,
            should_use_product_plans=should_use_product_plans,
            include_expanded_from=False,
            single_account=single_account,
            is_dry_run=is_dry_run,
            execution_mode=execution_mode,
            cache_invalidator=cache_invalidator,
        ),
        spoke_local_portfolios_tasks.SpokeLocalPortfolioSectionTask(
            manifest_file_path=f.name,
            puppet_account_id=puppet_account_id,
            should_use_sns=should_use_sns,
            should_use_product_plans=should_use_product_plans,
            include_expanded_from=False,
            single_account=single_account,
            is_dry_run=is_dry_run,
            execution_mode=execution_mode,
            cache_invalidator=cache_invalidator,
        ),
        lambda_invocations_tasks.LambdaInvocationsSectionTask(
            manifest_file_path=f.name,
            puppet_account_id=puppet_account_id,
            should_use_sns=should_use_sns,
            should_use_product_plans=should_use_product_plans,
            include_expanded_from=False,
            single_account=single_account,
            is_dry_run=is_dry_run,
            execution_mode=execution_mode,
            cache_invalidator=cache_invalidator,
        ),
    ]


def deploy(
    f,
    puppet_account_id,
    executor_account_id,
    single_account=None,
    num_workers=10,
    is_dry_run=False,
    is_list_launches=False,
    execution_mode="hub",
    on_complete_url=None,
):
    cache_invalidator = str(datetime.now())

    tasks_to_run = generate_tasks(
        f,
        puppet_account_id,
        executor_account_id,
        single_account,
        is_dry_run,
        execution_mode,
        cache_invalidator,
    )
    runner.run_tasks(
        puppet_account_id,
        executor_account_id,
        tasks_to_run,
        num_workers,
        is_dry_run,
        is_list_launches,
        execution_mode,
        cache_invalidator,
        on_complete_url,
    )


def graph(f):
    current_account_id = puppet_account_id = config.get_puppet_account_id()
    tasks_to_run = generate_tasks(f, puppet_account_id, current_account_id)
    lines = []
    nodes = []
    for task in tasks_to_run:
        nodes.append(task.graph_node())
        lines += task.get_graph_lines()
    click.echo("digraph G {\n")
    click.echo("node [shape=record fontname=Arial];")
    for node in nodes:
        click.echo(f"{node};")
    for line in lines:
        click.echo(f'{line} [label="depends on"];')
    click.echo("}")


def _do_bootstrap_spoke(
    puppet_account_id,
    cloudformation,
    puppet_version,
    permission_boundary,
    puppet_role_name,
    puppet_role_path,
):
    template = asset_helpers.read_from_site_packages(
        "{}-spoke.template.yaml".format(constants.BOOTSTRAP_STACK_NAME)
    )
    template = Template(template).render(VERSION=puppet_version)
    args = {
        "StackName": "{}-spoke".format(constants.BOOTSTRAP_STACK_NAME),
        "TemplateBody": template,
        "Capabilities": ["CAPABILITY_NAMED_IAM"],
        "Parameters": [
            {
                "ParameterKey": "PuppetAccountId",
                "ParameterValue": str(puppet_account_id),
            },
            {
                "ParameterKey": "PermissionBoundary",
                "ParameterValue": permission_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "Version",
                "ParameterValue": puppet_version,
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
        "Tags": [{"Key": "ServiceCatalogPuppet:Actor", "Value": "Framework",}],
    }
    cloudformation.create_or_update(**args)
    logger.info("Finished bootstrap of spoke")


def bootstrap_spoke_as(
    puppet_account_id,
    iam_role_arns,
    permission_boundary,
    puppet_role_name,
    puppet_role_path,
):
    cross_accounts = []
    index = 0
    for role in iam_role_arns:
        cross_accounts.append((role, "bootstrapping-role-{}".format(index)))
        index += 1

    with betterboto_client.CrossMultipleAccountsClientContextManager(
        "cloudformation", cross_accounts
    ) as cloudformation:
        _do_bootstrap_spoke(
            puppet_account_id,
            cloudformation,
            config.get_puppet_version(),
            permission_boundary,
            puppet_role_name,
            puppet_role_path,
        )


def _do_bootstrap(
    puppet_version,
    puppet_account_id,
    with_manual_approvals,
    puppet_code_pipeline_role_permission_boundary,
    source_role_permissions_boundary,
    puppet_generate_role_permission_boundary,
    puppet_deploy_role_permission_boundary,
    puppet_provisioning_role_permissions_boundary,
    cloud_formation_deploy_role_permissions_boundary,
    deploy_environment_compute_type,
    deploy_num_workers,
    source_provider,
    owner,
    repo,
    branch,
    poll_for_source_changes,
    webhook_secret,
    puppet_role_name,
    puppet_role_path,
):
    click.echo("Starting bootstrap")
    should_use_eventbridge = config.get_should_use_eventbridge(
        puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
    )
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
        template = asset_helpers.read_from_site_packages(
            "{}.template.yaml".format(
                "{}-regional".format(constants.BOOTSTRAP_STACK_NAME)
            )
        )
        template = Template(template).render(VERSION=puppet_version)
        args = {
            "StackName": "{}-regional".format(constants.BOOTSTRAP_STACK_NAME),
            "TemplateBody": template,
            "Capabilities": ["CAPABILITY_IAM"],
            "Parameters": [
                {
                    "ParameterKey": "Version",
                    "ParameterValue": puppet_version,
                    "UsePreviousValue": False,
                },
                {
                    "ParameterKey": "DefaultRegionValue",
                    "ParameterValue": os.environ.get("AWS_DEFAULT_REGION"),
                    "UsePreviousValue": False,
                },
            ],
            "Tags": [{"Key": "ServiceCatalogPuppet:Actor", "Value": "Framework",}],
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
            {"Configuration": {"RepositoryName": repo, "BranchName": branch,},}
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

    with betterboto_client.ClientContextManager("cloudformation") as cloudformation:
        click.echo("Creating {}".format(constants.BOOTSTRAP_STACK_NAME))
        template = asset_helpers.read_from_site_packages(
            "{}.template.yaml".format(constants.BOOTSTRAP_STACK_NAME)
        )
        template = Template(template).render(
            VERSION=puppet_version,
            ALL_REGIONS=all_regions,
            Source=source_args,
            is_caching_enabled=config.is_caching_enabled(
                puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
            ),
        )
        template = Template(template).render(
            VERSION=puppet_version, ALL_REGIONS=all_regions, Source=source_args
        )
        args = {
            "StackName": constants.BOOTSTRAP_STACK_NAME,
            "TemplateBody": template,
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Parameters": [
                {
                    "ParameterKey": "Version",
                    "ParameterValue": puppet_version,
                    "UsePreviousValue": False,
                },
                {
                    "ParameterKey": "OrgIamRoleArn",
                    "ParameterValue": str(
                        config.get_org_iam_role_arn(puppet_account_id)
                    ),
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
        }
        cloudformation.create_or_update(**args)

    click.echo("Finished creating {}.".format(constants.BOOTSTRAP_STACK_NAME))
    if source_provider == "CodeCommit":
        with betterboto_client.ClientContextManager("codecommit") as codecommit:
            response = codecommit.get_repository(repositoryName=repo)
            clone_url = response.get("repositoryMetadata").get("cloneUrlHttp")
            clone_command = (
                "git clone --config 'credential.helper=!aws codecommit credential-helper $@' "
                "--config 'credential.UseHttpPath=true' {}".format(clone_url)
            )
            click.echo(
                "You need to clone your newly created repo now and will then need to seed it: \n{}".format(
                    clone_command
                )
            )


def bootstrap_spoke(
    puppet_account_id, permission_boundary, puppet_role_name, puppet_role_path
):
    with betterboto_client.ClientContextManager("cloudformation") as cloudformation:
        _do_bootstrap_spoke(
            puppet_account_id,
            cloudformation,
            config.get_puppet_version(),
            permission_boundary,
            puppet_role_name,
            puppet_role_path,
        )


def bootstrap_branch(
    branch_to_bootstrap,
    puppet_account_id,
    with_manual_approvals,
    puppet_code_pipeline_role_permission_boundary,
    source_role_permissions_boundary,
    puppet_generate_role_permission_boundary,
    puppet_deploy_role_permission_boundary,
    puppet_provisioning_role_permissions_boundary,
    cloud_formation_deploy_role_permissions_boundary,
    deploy_num_workers,
    source_provider,
    owner,
    repo,
    branch,
    poll_for_source_changes,
    webhook_secret,
    puppet_role_name,
    puppet_role_path,
):
    _do_bootstrap(
        "https://github.com/awslabs/aws-service-catalog-puppet/archive/{}.zip".format(
            branch_to_bootstrap
        ),
        puppet_account_id,
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        constants.DEPLOY_ENVIRONMENT_COMPUTE_TYPE_DEFAULT,
        deploy_num_workers,
        source_provider,
        owner,
        repo,
        branch,
        poll_for_source_changes,
        webhook_secret,
        puppet_role_name,
        puppet_role_path,
    )


def bootstrap(
    with_manual_approvals,
    puppet_account_id,
    puppet_code_pipeline_role_permission_boundary,
    source_role_permissions_boundary,
    puppet_generate_role_permission_boundary,
    puppet_deploy_role_permission_boundary,
    puppet_provisioning_role_permissions_boundary,
    cloud_formation_deploy_role_permissions_boundary,
    deploy_environment_compute_type,
    deploy_num_workers,
    source_provider,
    owner,
    repo,
    branch,
    poll_for_source_changes,
    webhook_secret,
    puppet_role_name,
    puppet_role_path,
):
    _do_bootstrap(
        config.get_puppet_version(),
        puppet_account_id,
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type,
        deploy_num_workers,
        source_provider,
        owner,
        repo,
        branch,
        poll_for_source_changes,
        webhook_secret,
        puppet_role_name,
        puppet_role_path,
    )


def seed(complexity, p):
    example = "manifest-{}.yaml".format(complexity)
    shutil.copy2(
        asset_helpers.resolve_from_site_packages(
            os.path.sep.join(["manifests", example])
        ),
        os.path.sep.join([p, "manifest.yaml"]),
    )


def expand(f, single_account):
    click.echo("Expanding")
    puppet_account_id = config.get_puppet_account_id()
    manifest = manifest_utils.load(f, puppet_account_id)
    org_iam_role_arn = config.get_org_iam_role_arn(puppet_account_id)
    if org_iam_role_arn is None:
        click.echo("No org role set - not expanding")
        new_manifest = manifest
    else:
        click.echo("Expanding using role: {}".format(org_iam_role_arn))
        with betterboto_client.CrossAccountClientContextManager(
            "organizations", org_iam_role_arn, "org-iam-role"
        ) as client:
            new_manifest = manifest_utils.expand_manifest(manifest, client)
    click.echo("Expanded")
    if single_account:
        click.echo(f"Filtering for single account: {single_account}")

        for account in new_manifest.get("accounts", []):
            if account.get("account_id") == single_account:
                click.echo(f"Found single account: {single_account}")
                new_manifest["accounts"] = [account]
                break

        click.echo("Filtered")

    new_name = f.name.replace(".yaml", "-expanded.yaml")
    logger.info("Writing new manifest: {}".format(new_name))
    with open(new_name, "w") as output:
        output.write(yaml.safe_dump(new_manifest, default_flow_style=False))


def validate(f):
    logger.info("Validating {}".format(f.name))
    c = Core(
        source_file=f.name,
        schema_files=[asset_helpers.resolve_from_site_packages("schema.yaml")],
        extensions=[
            asset_helpers.resolve_from_site_packages("puppet_schema_extensions.py")
        ],
    )
    c.validate(raise_exception=True)
    click.echo("Finished validating: {}".format(f.name))
    click.echo("Finished validating: OK")


def version():
    click.echo(
        "cli version: {}".format(
            pkg_resources.require("aws-service-catalog-puppet")[0].version
        )
    )
    with betterboto_client.ClientContextManager("ssm") as ssm:
        response = ssm.get_parameter(Name="service-catalog-puppet-regional-version")
        click.echo(
            "regional stack version: {} for region: {}".format(
                response.get("Parameter").get("Value"),
                response.get("Parameter").get("ARN").split(":")[3],
            )
        )
        response = ssm.get_parameter(Name="service-catalog-puppet-version")
        click.echo("stack version: {}".format(response.get("Parameter").get("Value"),))


def upload_config(config):
    with betterboto_client.ClientContextManager("ssm") as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME,
            Type="String",
            Value=yaml.safe_dump(config),
            Overwrite=True,
        )
    click.echo("Uploaded config")


def set_org_iam_role_arn(org_iam_role_arn):
    with betterboto_client.ClientContextManager("ssm") as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN,
            Type="String",
            Value=org_iam_role_arn,
            Overwrite=True,
        )
    click.echo("Uploaded config")


def bootstrap_org_master(puppet_account_id):
    with betterboto_client.ClientContextManager("cloudformation",) as cloudformation:
        org_iam_role_arn = None
        puppet_version = config.get_puppet_version()
        logger.info("Starting bootstrap of org master")
        stack_name = f"{constants.BOOTSTRAP_STACK_NAME}-org-master-{puppet_account_id}"
        template = asset_helpers.read_from_site_packages(
            f"{constants.BOOTSTRAP_STACK_NAME}-org-master.template.yaml"
        )
        template = Template(template).render(
            VERSION=puppet_version, puppet_account_id=puppet_account_id
        )
        args = {
            "StackName": stack_name,
            "TemplateBody": template,
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Parameters": [
                {
                    "ParameterKey": "PuppetAccountId",
                    "ParameterValue": str(puppet_account_id),
                },
                {
                    "ParameterKey": "Version",
                    "ParameterValue": puppet_version,
                    "UsePreviousValue": False,
                },
            ],
            "Tags": [{"Key": "ServiceCatalogPuppet:Actor", "Value": "Framework",}],
        }
        cloudformation.create_or_update(**args)
        response = cloudformation.describe_stacks(StackName=stack_name)
        if len(response.get("Stacks")) != 1:
            raise Exception("Expected there to be only one {} stack".format(stack_name))
        stack = response.get("Stacks")[0]

        for output in stack.get("Outputs"):
            if output.get("OutputKey") == constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN:
                logger.info("Finished bootstrap of org-master")
                org_iam_role_arn = output.get("OutputValue")

        if org_iam_role_arn is None:
            raise Exception(
                "Could not find output: {} in stack: {}".format(
                    constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN, stack_name
                )
            )

    click.echo("Bootstrapped org master, org-iam-role-arn: {}".format(org_iam_role_arn))


def run(what, tail):
    pipelines = {"puppet": constants.PIPELINE_NAME}
    pipeline_name = pipelines.get(what)
    pipeline_execution_id = aws.run_pipeline(pipeline_name, tail)
    click.echo(
        f"https://{os.environ.get('AWS_DEFAULT_REGION')}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline_name}/executions/{pipeline_execution_id}/timeline"
    )


def list_resources():
    click.echo("# Framework resources")

    click.echo("## SSM Parameters used")
    click.echo(f"- {constants.CONFIG_PARAM_NAME}")
    click.echo(f"- {constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN}")

    for file in Path(__file__).parent.resolve().glob("*.template.yaml"):
        if "empty.template.yaml" == file.name:
            continue
        template_contents = Template(open(file, "r").read()).render()
        template = cfn_tools.load_yaml(template_contents)
        click.echo(f"## Resources for stack: {file.name.split('.')[0]}")
        table_data = [
            ["Logical Name", "Resource Type", "Name",],
        ]
        table = terminaltables.AsciiTable(table_data)
        for logical_name, resource in template.get("Resources").items():
            resource_type = resource.get("Type")
            name = "-"
            type_to_name = {
                "AWS::IAM::Role": "RoleName",
                "AWS::SSM::Parameter": "Name",
                "AWS::S3::Bucket": "BucketName",
                "AWS::CodePipeline::Pipeline": "Name",
                "AWS::CodeBuild::Project": "Name",
                "AWS::CodeCommit::Repository": "RepositoryName",
                "AWS::SNS::Topic": "TopicName",
                "AWS::SQS::Queue": "QueueName",
            }

            if type_to_name.get(resource_type) is not None:
                name = resource.get("Properties", {}).get(
                    type_to_name.get(resource_type), "Not Specified"
                )
                if not isinstance(name, str):
                    name = cfn_tools.dump_yaml(name)

            table_data.append([logical_name, resource_type, name])

        click.echo(table.table)
    click.echo(f"n.b. AWS::StackName evaluates to {constants.BOOTSTRAP_STACK_NAME}")


def import_product_set(f, name, portfolio_name):
    url = f"https://raw.githubusercontent.com/awslabs/aws-service-catalog-products/master/{name}/manifest.yaml"
    response = requests.get(url)
    logger.info(f"Getting {url}")
    manifest = yaml.safe_load(f.read())
    if manifest.get("launches") is None:
        manifest["launches"] = {}
    manifest_segment = yaml.safe_load(response.text)
    for launch_name, details in manifest_segment.get("launches").items():
        details["portfolio"] = portfolio_name
        manifest["launches"][launch_name] = details
    with open(f.name, "w") as f:
        f.write(yaml.safe_dump(manifest))


def get_manifest():
    with betterboto_client.ClientContextManager("codecommit") as codecommit:
        content = codecommit.get_file(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            filePath="manifest.yaml",
        ).get("fileContent")
        return yaml.safe_load(content)


def save_manifest(manifest):
    with betterboto_client.ClientContextManager("codecommit") as codecommit:
        parent_commit_id = (
            codecommit.get_branch(
                repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
                branchName="master",
            )
            .get("branch")
            .get("commitId")
        )
        codecommit.put_file(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            branchName="master",
            fileContent=yaml.safe_dump(manifest),
            parentCommitId=parent_commit_id,
            commitMessage="Auto generated commit",
            filePath=f"manifest.yaml",
        )


def add_to_accounts(account_or_ou):
    manifest = get_manifest()
    manifest.get("accounts").append(account_or_ou)
    save_manifest(manifest)


def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    manifest = get_manifest()
    for account in manifest.get("accounts", []):
        if account.get("account_id", "") == account_id_or_ou_id_or_ou_path:
            manifest.get("accounts").remove(account)
            return save_manifest(manifest)
        elif account.get("ou", "") == account_id_or_ou_id_or_ou_path:
            manifest.get("accounts").remove(account)
            return save_manifest(manifest)
    raise Exception(f"Did not remove {account_id_or_ou_id_or_ou_path}")


def add_to_launches(launch_name, launch):
    manifest = get_manifest()
    launches = manifest.get("launches", {})
    launches[launch_name] = launch
    manifest["launches"] = launches
    save_manifest(manifest)


def remove_from_launches(launch_name):
    manifest = get_manifest()
    del manifest.get("launches")[launch_name]
    save_manifest(manifest)


def set_config_value(name, value):
    with betterboto_client.ClientContextManager(
        "ssm", region_name=constants.HOME_REGION
    ) as ssm:
        try:
            response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
            config = yaml.safe_load(response.get("Parameter").get("Value"))
        except ssm.exceptions.ParameterNotFound:
            config = {}

        if name == "regions":
            config["regions"] = value if len(value) > 1 else value[0].split(",")
        else:
            config[name] = value.upper() == "TRUE"

        upload_config(config)


def set_named_config_value(name, value):
    with betterboto_client.ClientContextManager(
        "ssm", region_name=constants.HOME_REGION
    ) as ssm:
        ssm.put_parameter(
            Name=name, Type="String", Value=value, Overwrite=True,
        )
        click.echo("Uploaded named config")


def bootstrap_spokes_in_ou(
    ou_path_or_id,
    role_name,
    iam_role_arns,
    permission_boundary,
    num_workers,
    puppet_role_name,
    puppet_role_path,
):
    puppet_account_id = config.get_puppet_account_id()
    org_iam_role_arn = config.get_org_iam_role_arn(puppet_account_id)
    if org_iam_role_arn is None:
        click.echo("No org role set - not expanding")
    else:
        click.echo("Expanding using role: {}".format(org_iam_role_arn))
        with betterboto_client.CrossAccountClientContextManager(
            "organizations", org_iam_role_arn, "org-iam-role"
        ) as client:
            tasks = []
            if ou_path_or_id.startswith("/"):
                ou_id = client.convert_path_to_ou(ou_path_or_id)
            else:
                ou_id = ou_path_or_id
            logging.info(f"ou_id is {ou_id}")
            response = client.list_children_nested(ParentId=ou_id, ChildType="ACCOUNT")
            for spoke in response:
                tasks.append(
                    management_tasks.BootstrapSpokeAsTask(
                        puppet_account_id=puppet_account_id,
                        account_id=spoke.get("Id"),
                        iam_role_arns=iam_role_arns,
                        role_name=role_name,
                        permission_boundary=permission_boundary,
                        puppet_role_name=puppet_role_name,
                        puppet_role_path=puppet_role_path,
                    )
                )

        runner.run_tasks_for_bootstrap_spokes_in_ou(tasks, num_workers)


def handle_action_execution_detail(puppet_account_id, action_execution_detail):
    action_type_id = action_execution_detail.get("input").get("actionTypeId")
    if (
        action_type_id.get("category") == "Build"
        and action_type_id.get("owner") == "AWS"
        and action_type_id.get("provider") == "CodeBuild"
    ):
        external_execution_id = (
            action_execution_detail.get("output")
            .get("executionResult")
            .get("externalExecutionId")
        )

        with betterboto_client.ClientContextManager(
            "codebuild", region_name=config.get_home_region(puppet_account_id)
        ) as codebuild:
            builds = codebuild.batch_get_builds(ids=[external_execution_id]).get(
                "builds"
            )
            build = builds[0]
            log_details = build.get("logs")
            with betterboto_client.ClientContextManager(
                "logs", region_name=config.get_home_region(puppet_account_id)
            ) as logs:
                with open(
                    f"log-{action_execution_detail.get('input').get('configuration').get('ProjectName')}.log",
                    "w",
                ) as f:
                    params = {
                        "logGroupName": log_details.get("groupName"),
                        "logStreamName": log_details.get("streamName"),
                        "startFromHead": True,
                    }
                    has_more_logs = True
                    while has_more_logs:
                        get_log_events_response = logs.get_log_events(**params)
                        if (len(get_log_events_response.get("events"))) > 0:
                            params["nextToken"] = get_log_events_response.get(
                                "nextForwardToken"
                            )
                        else:
                            has_more_logs = False
                            if params.get("nextToken"):
                                del params["nextToken"]
                        for e in get_log_events_response.get("events"):
                            d = datetime.utcfromtimestamp(
                                e.get("timestamp") / 1000
                            ).strftime("%Y-%m-%d %H:%M:%S")
                            f.write(f"{d} : {e.get('message')}")


def export_puppet_pipeline_logs(execution_id, puppet_account_id):
    with betterboto_client.ClientContextManager(
        "codepipeline", region_name=config.get_home_region(puppet_account_id)
    ) as codepipeline:
        action_execution_details = codepipeline.list_action_executions(
            pipelineName=constants.PIPELINE_NAME,
            filter={"pipelineExecutionId": execution_id},
        ).get("actionExecutionDetails")

        for action_execution_detail in action_execution_details:
            handle_action_execution_detail(puppet_account_id, action_execution_detail)


def uninstall(puppet_account_id):
    with betterboto_client.ClientContextManager(
        "cloudformation", region_name=config.get_home_region(puppet_account_id)
    ) as cloudformation:
        cloudformation.ensure_deleted(StackName=constants.BOOTSTRAP_STACK_NAME)


def release_spoke(puppet_account_id):
    with betterboto_client.ClientContextManager(
        "cloudformation", region_name=config.get_home_region(puppet_account_id)
    ) as cloudformation:
        cloudformation.ensure_deleted(
            StackName=f"{constants.BOOTSTRAP_STACK_NAME}-spoke"
        )


def wait_for_code_build_in(iam_role_arns):
    cross_accounts = []
    index = 0
    for role in iam_role_arns:
        cross_accounts.append((role, "waiting-for-code-build-{}".format(index)))
        index += 1

    with betterboto_client.CrossMultipleAccountsClientContextManager(
        "codebuild", cross_accounts
    ) as codebuild:
        while True:
            try:
                result = codebuild.list_projects()
                logger.info(f"Was able to list projects: {result}")
                break
            except Exception as e:
                logger.error("type error: " + str(e))
                logger.error(traceback.format_exc())


def wait_for_cloudformation_in(iam_role_arns):
    cross_accounts = []
    index = 0
    for role in iam_role_arns:
        cross_accounts.append((role, "waiting-for-cloudformation-{}".format(index)))
        index += 1

    with betterboto_client.CrossMultipleAccountsClientContextManager(
        "cloudformation", cross_accounts
    ) as cloudformation:
        while True:
            try:
                result = cloudformation.list_stacks()
                logger.info(f"Was able to list stacks: {result}")
                break
            except Exception as e:
                logger.error("type error: " + str(e))
                logger.error(traceback.format_exc())
