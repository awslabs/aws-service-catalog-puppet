# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import cfn_tools
import requests
from colorclass import Color
import terminaltables

import shutil
import json
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
from servicecatalog_puppet import manifest_utils_for_spoke_local_portfolios
from servicecatalog_puppet.workflow import management as management_tasks
from servicecatalog_puppet.workflow import portfoliomanagement as portfoliomanagement_tasks
from servicecatalog_puppet.workflow import provisioning as provisioning_tasks
from servicecatalog_puppet.workflow import runner as runner
from servicecatalog_puppet import config
from servicecatalog_puppet import manifest_utils
from servicecatalog_puppet import aws

from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import constants

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def cli(info, info_line_numbers):
    if info:
        logging.basicConfig(
            format='%(levelname)s %(threadName)s %(message)s', level=logging.INFO
        )
    if info_line_numbers:
        logging.basicConfig(
            format='%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO
        )


def generate_shares(f):
    logger.info('Starting to generate shares for: {}'.format(f.name))
    tasks_to_run = []
    puppet_account_id = config.get_puppet_account_id()
    manifest = manifest_utils.load(f)
    accounts_by_id = {}
    for account in manifest.get('accounts'):
        accounts_by_id[account.get('account_id')] = account

    launch_tasks = manifest_utils_for_launches.generate_launch_tasks(
        manifest, puppet_account_id, False, False, include_expanded_from=False, single_account=None, is_dry_run=False
    )

    for launch_task in launch_tasks:
        t = manifest_utils_for_launches.generate_launch_task_defs_for_launch(
            launch_task.launch_name,
            launch_task.manifest,
            launch_task.puppet_account_id,
            launch_task.should_use_sns,
            launch_task.should_use_product_plans,
            launch_task.include_expanded_from,
            launch_task.single_account,
            launch_task.is_dry_run
        )
        tasks = launch_task.generate_provisions(t.get('task_defs'))
        for task_ in tasks:
            task = task_.param_kwargs
            a_id = task.get('account_id')
            tasks_to_run.append(
                portfoliomanagement_tasks.CreateShareForAccountLaunchRegion(
                    puppet_account_id=puppet_account_id,
                    account_id=a_id,
                    region=task.get('region'),
                    portfolio=task.get('portfolio'),
                    expanded_from=accounts_by_id.get(a_id).get('expanded_from'),
                    organization=accounts_by_id.get(a_id).get('organization'),
                )
            )

    spoke_local_portfolios_tasks = manifest_utils_for_spoke_local_portfolios.generate_spoke_local_portfolios_tasks(
        manifest, puppet_account_id, False, False, include_expanded_from=False, single_account=None, is_dry_run=False
    )

    # TODO fixme
    for spoke_local_portfolios_task in spoke_local_portfolios_tasks:
        t = manifest_utils_for_spoke_local_portfolios.generate_spoke_local_portfolios_tasks_for_spoke_local_portfolio(
            spoke_local_portfolios_task.spoke_local_portfolio_name,
            spoke_local_portfolios_task.manifest,
            spoke_local_portfolios_task.puppet_account_id,
            spoke_local_portfolios_task.should_use_sns,
            spoke_local_portfolios_task.should_use_product_plans,
            spoke_local_portfolios_task.include_expanded_from,
            spoke_local_portfolios_task.single_account,
            spoke_local_portfolios_task.is_dry_run,
        )

        sub_tasks = spoke_local_portfolios_task.generate_tasks(t.get('task_defs'))
        for sub_task in sub_tasks:
            if isinstance(sub_task, portfoliomanagement_tasks.CreateSpokeLocalPortfolioTask):
                param_kwargs = sub_task.param_kwargs
                a_id = param_kwargs.get('account_id')
                tasks_to_run.append(
                    portfoliomanagement_tasks.CreateShareForAccountLaunchRegion(
                        puppet_account_id=puppet_account_id,
                        account_id=param_kwargs.get('account_id'),
                        region=param_kwargs.get('region'),
                        portfolio=param_kwargs.get('portfolio'),
                        expanded_from=accounts_by_id.get(a_id).get('expanded_from'),
                        organization=accounts_by_id.get(a_id).get('organization'),
                    )
                )

    runner.run_tasks_for_generate_shares(tasks_to_run)


def reset_provisioned_product_owner(f):
    puppet_account_id = config.get_puppet_account_id()
    manifest = manifest_utils.load(f)

    task_defs = manifest_utils_for_launches.generate_launch_tasks(
        manifest, puppet_account_id, False, False
    )

    tasks_to_run = []
    for task in task_defs:
        task_status = task.get('status')
        if task_status == constants.PROVISIONED:
            tasks_to_run.append(
                provisioning_tasks.ResetProvisionedProductOwnerTask(
                    launch_name=task.get('launch_name'),
                    account_id=task.get('account_id'),
                    region=task.get('region'),
                )
            )

    runner.run_tasks(tasks_to_run, 10)


def generate_tasks(f, single_account=None, is_dry_run=False):
    puppet_account_id = config.get_puppet_account_id()
    manifest = manifest_utils.load(f)

    should_use_sns = config.get_should_use_sns(os.environ.get("AWS_DEFAULT_REGION"))
    should_use_product_plans = config.get_should_use_product_plans(os.environ.get("AWS_DEFAULT_REGION"))

    tasks_to_run = manifest_utils_for_launches.generate_launch_tasks(
        manifest,
        puppet_account_id,
        should_use_sns,
        should_use_product_plans,
        include_expanded_from=False,
        single_account=single_account,
        is_dry_run=is_dry_run,
    )
    logger.info("Finished generating provisioning tasks")

    if not is_dry_run:
        logger.info("Generating sharing tasks")
        spoke_local_portfolios_tasks = manifest_utils_for_spoke_local_portfolios.generate_spoke_local_portfolios_tasks(
            manifest,
            puppet_account_id,
            should_use_sns,
            should_use_product_plans,
            include_expanded_from=False,
            single_account=single_account,
            is_dry_run=is_dry_run,
        )
        tasks_to_run += spoke_local_portfolios_tasks
        logger.info("Finished generating sharing tasks")

    logger.info("Finished generating all tasks")
    return tasks_to_run


def deploy(f, single_account, num_workers=10, is_dry_run=False):
    tasks_to_run = generate_tasks(f, single_account, is_dry_run)
    runner.run_tasks(tasks_to_run, num_workers, is_dry_run)


def graph(f):
    tasks_to_run = generate_tasks(f)
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
        click.echo(f"{line} [label=\"depends on\"];")
    click.echo("}")


def _do_bootstrap_spoke(puppet_account_id, cloudformation, puppet_version, permission_boundary):
    logger.info('Starting bootstrap of spoke')
    template = asset_helpers.read_from_site_packages('{}-spoke.template.yaml'.format(constants.BOOTSTRAP_STACK_NAME))
    template = Template(template).render(VERSION=puppet_version)
    args = {
        'StackName': "{}-spoke".format(constants.BOOTSTRAP_STACK_NAME),
        'TemplateBody': template,
        'Capabilities': ['CAPABILITY_NAMED_IAM'],
        'Parameters': [
            {
                'ParameterKey': 'PuppetAccountId',
                'ParameterValue': str(puppet_account_id),
            }, {
                'ParameterKey': 'PermissionBoundary',
                'ParameterValue': permission_boundary,
                'UsePreviousValue': False,
            }, {
                'ParameterKey': 'Version',
                'ParameterValue': puppet_version,
                'UsePreviousValue': False,
            },
        ],
        'Tags': [
            {
                "Key": "ServiceCatalogPuppet:Actor",
                "Value": "Framework",
            }
        ]
    }
    cloudformation.create_or_update(**args)
    logger.info('Finished bootstrap of spoke')


def bootstrap_spoke_as(puppet_account_id, iam_role_arns, permission_boundary):
    cross_accounts = []
    index = 0
    for role in iam_role_arns:
        cross_accounts.append(
            (role, 'bootstrapping-role-{}'.format(index))
        )
        index += 1

    with betterboto_client.CrossMultipleAccountsClientContextManager(
            'cloudformation',
            cross_accounts
    ) as cloudformation:
        _do_bootstrap_spoke(
            puppet_account_id,
            cloudformation,
            config.get_puppet_version(),
            permission_boundary
        )


def _do_bootstrap(
        puppet_version,
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type="BUILD_GENERAL1_SMALL",
        deploy_num_workers=10,
):
    click.echo('Starting bootstrap')

    should_use_eventbridge = config.get_should_use_eventbridge(os.environ.get("AWS_DEFAULT_REGION"))
    if should_use_eventbridge:
        with betterboto_client.ClientContextManager('events') as events:
            try:
                events.describe_event_bus(Name=constants.EVENT_BUS_NAME)
            except events.exceptions.ResourceNotFoundException:
                events.create_event_bus(
                    Name=constants.EVENT_BUS_NAME,
                )

    all_regions = config.get_regions(os.environ.get("AWS_DEFAULT_REGION"))
    with betterboto_client.MultiRegionClientContextManager('cloudformation', all_regions) as clients:
        click.echo('Creating {}-regional'.format(constants.BOOTSTRAP_STACK_NAME))
        threads = []
        template = asset_helpers.read_from_site_packages(
            '{}.template.yaml'.format('{}-regional'.format(constants.BOOTSTRAP_STACK_NAME)))
        template = Template(template).render(VERSION=puppet_version)
        args = {
            'StackName': '{}-regional'.format(constants.BOOTSTRAP_STACK_NAME),
            'TemplateBody': template,
            'Capabilities': ['CAPABILITY_IAM'],
            'Parameters': [
                {
                    'ParameterKey': 'Version',
                    'ParameterValue': puppet_version,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'DefaultRegionValue',
                    'ParameterValue': os.environ.get('AWS_DEFAULT_REGION'),
                    'UsePreviousValue': False,
                },
            ],
            'Tags': [
                {
                    "Key": "ServiceCatalogPuppet:Actor",
                    "Value": "Framework",
                }
            ]
        }
        for client_region, client in clients.items():
            process = Thread(name=client_region, target=client.create_or_update, kwargs=args)
            process.start()
            threads.append(process)
        for process in threads:
            process.join()
        click.echo('Finished creating {}-regional'.format(constants.BOOTSTRAP_STACK_NAME))

    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        click.echo('Creating {}'.format(constants.BOOTSTRAP_STACK_NAME))
        template = asset_helpers.read_from_site_packages('{}.template.yaml'.format(constants.BOOTSTRAP_STACK_NAME))
        template = Template(template).render(VERSION=puppet_version, ALL_REGIONS=all_regions)
        args = {
            'StackName': constants.BOOTSTRAP_STACK_NAME,
            'TemplateBody': template,
            'Capabilities': ['CAPABILITY_NAMED_IAM'],
            'Parameters': [
                {
                    'ParameterKey': 'Version',
                    'ParameterValue': puppet_version,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'OrgIamRoleArn',
                    'ParameterValue': str(config.get_org_iam_role_arn()),
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'WithManualApprovals',
                    'ParameterValue': "Yes" if with_manual_approvals else "No",
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'PuppetCodePipelineRolePermissionBoundary',
                    'ParameterValue': puppet_code_pipeline_role_permission_boundary,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'SourceRolePermissionsBoundary',
                    'ParameterValue': source_role_permissions_boundary,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'PuppetGenerateRolePermissionBoundary',
                    'ParameterValue': puppet_generate_role_permission_boundary,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'PuppetDeployRolePermissionBoundary',
                    'ParameterValue': puppet_deploy_role_permission_boundary,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'PuppetProvisioningRolePermissionsBoundary',
                    'ParameterValue': puppet_provisioning_role_permissions_boundary,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'CloudFormationDeployRolePermissionsBoundary',
                    'ParameterValue': cloud_formation_deploy_role_permissions_boundary,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'DeployEnvironmentComputeType',
                    'ParameterValue': deploy_environment_compute_type,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'DeployNumWorkers',
                    'ParameterValue': str(deploy_num_workers),
                    'UsePreviousValue': False,
                },
            ],
        }
        cloudformation.create_or_update(**args)

    click.echo('Finished creating {}.'.format(constants.BOOTSTRAP_STACK_NAME))
    with betterboto_client.ClientContextManager('codecommit') as codecommit:
        response = codecommit.get_repository(repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME)
        clone_url = response.get('repositoryMetadata').get('cloneUrlHttp')
        clone_command = "git clone --config 'credential.helper=!aws codecommit credential-helper $@' " \
                        "--config 'credential.UseHttpPath=true' {}".format(clone_url)
        click.echo(
            'You need to clone your newly created repo now and will then need to seed it: \n{}'.format(
                clone_command
            )
        )


def bootstrap_spoke(puppet_account_id, permission_boundary):
    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        _do_bootstrap_spoke(
            puppet_account_id,
            cloudformation,
            config.get_puppet_version(),
            permission_boundary
        )


def bootstrap_branch(
        branch_name,
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
):
    _do_bootstrap(
        "https://github.com/awslabs/aws-service-catalog-puppet/archive/{}.zip".format(branch_name),
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
    )


def bootstrap(
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type,
        deploy_num_workers,
):
    _do_bootstrap(
        config.get_puppet_version(),
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type,
        deploy_num_workers,
    )


def seed(complexity, p):
    example = "manifest-{}.yaml".format(complexity)
    shutil.copy2(
        asset_helpers.resolve_from_site_packages(
            os.path.sep.join(['manifests', example])
        ),
        os.path.sep.join([p, "manifest.yaml"])
    )


def list_launches(f, format):
    manifest = manifest_utils.load(f)
    if format == "table":
        click.echo("Getting details from your account...")
    all_regions = config.get_regions(os.environ.get("AWS_DEFAULT_REGION"))
    account_ids = [a.get('account_id') for a in manifest.get('accounts')]
    deployments = {}
    for account_id in account_ids:
        for region_name in all_regions:
            role = "arn:aws:iam::{}:role/{}".format(account_id, 'servicecatalog-puppet/PuppetRole')
            logger.info("Looking at region: {} in account: {}".format(region_name, account_id))
            with betterboto_client.CrossAccountClientContextManager(
                    'servicecatalog', role, 'sc-{}-{}'.format(account_id, region_name), region_name=region_name
            ) as spoke_service_catalog:
                response = spoke_service_catalog.list_accepted_portfolio_shares()
                portfolios = response.get('PortfolioDetails', [])
                response = spoke_service_catalog.list_portfolios()
                portfolios += response.get('PortfolioDetails', [])

                for portfolio in portfolios:
                    portfolio_id = portfolio.get('Id')
                    response = spoke_service_catalog.search_products_as_admin(PortfolioId=portfolio_id)
                    for product_view_detail in response.get('ProductViewDetails', []):
                        product_view_summary = product_view_detail.get('ProductViewSummary')
                        product_id = product_view_summary.get('ProductId')
                        response = spoke_service_catalog.search_provisioned_products(
                            Filters={'SearchQuery': ["productId:{}".format(product_id)]})
                        for provisioned_product in response.get('ProvisionedProducts', []):
                            launch_name = provisioned_product.get('Name')
                            status = provisioned_product.get('Status')

                            provisioning_artifact_response = spoke_service_catalog.describe_provisioning_artifact(
                                ProvisioningArtifactId=provisioned_product.get('ProvisioningArtifactId'),
                                ProductId=provisioned_product.get('ProductId'),
                            ).get('ProvisioningArtifactDetail')

                            if deployments.get(account_id) is None:
                                deployments[account_id] = {'account_id': account_id, constants.LAUNCHES: {}}

                            if deployments[account_id][constants.LAUNCHES].get(launch_name) is None:
                                deployments[account_id][constants.LAUNCHES][launch_name] = {}

                            deployments[account_id][constants.LAUNCHES][launch_name][region_name] = {
                                'launch_name': launch_name,
                                'portfolio': portfolio.get('DisplayName'),
                                'product': manifest.get(constants.LAUNCHES, {}).get(launch_name, {}).get('product'),
                                'version': provisioning_artifact_response.get('Name'),
                                'active': provisioning_artifact_response.get('Active'),
                                'region': region_name,
                                'status': status,
                            }
                            output_path = os.path.sep.join([
                                constants.LAUNCHES_PATH,
                                account_id,
                                region_name,
                            ])
                            if not os.path.exists(output_path):
                                os.makedirs(output_path)

                            output = os.path.sep.join([output_path, "{}.json".format(provisioned_product.get('Id'))])
                            with open(output, 'w') as f:
                                f.write(json.dumps(
                                    provisioned_product,
                                    indent=4, default=str
                                ))

    results = {}
    tasks = generate_tasks(f)
    # deployments[account_id][constants.LAUNCHES][launch_name][region_name]
    for task in tasks:
        account_id = task.get('account_id')
        launch_name = task.get('launch_name')
        if deployments.get(account_id, {}).get(constants.LAUNCHES, {}).get(launch_name) is None:
            pass
        else:
            for region, regional_details in deployments[account_id][constants.LAUNCHES][launch_name].items():
                results[f"{account_id}_{region}_{launch_name}"] = {
                    'account_id': account_id,
                    'region': region,
                    'launch': launch_name,
                    'portfolio': regional_details.get('portfolio'),
                    'product': regional_details.get('product'),
                    'expected_version': task.get('version'),
                    'actual_version': regional_details.get('version'),
                    'active': regional_details.get('active'),
                    'status': regional_details.get('status'),
                }

    if format == "table":
        table = [
            [
                'account_id',
                'region',
                'launch',
                'portfolio',
                'product',
                'expected_version',
                'actual_version',
                'active',
                'status',
            ]
        ]

        for result in results.values():
            table.append([
                result.get('account_id'),
                result.get('region'),
                result.get('launch'),
                result.get('portfolio'),
                result.get('product'),
                result.get('expected_version'),
                Color("{green}" + result.get('actual_version') + "{/green}") if result.get(
                    'actual_version') == result.get('expected_version') else Color(
                    "{red}" + result.get('actual_version') + "{/red}"),
                Color("{green}" + str(result.get('active')) + "{/green}") if result.get('active') else Color(
                    "{red}" + str(result.get('active')) + "{/red}"),
                Color("{green}" + result.get('status') + "{/green}") if result.get('status') == "AVAILABLE" else Color(
                    "{red}" + result.get('status') + "{/red}")
            ])
        click.echo(terminaltables.AsciiTable(table).table)

    elif format == "json":
        click.echo(
            json.dumps(
                results,
                indent=4,
                default=str,
            )
        )

    else:
        raise Exception(f"Unsupported format: {format}")


def expand(f):
    click.echo('Expanding')
    manifest = manifest_utils.load(f)
    org_iam_role_arn = config.get_org_iam_role_arn()
    if org_iam_role_arn is None:
        click.echo('No org role set - not expanding')
        new_manifest = manifest
    else:
        click.echo('Expanding using role: {}'.format(org_iam_role_arn))
        with betterboto_client.CrossAccountClientContextManager(
                'organizations', org_iam_role_arn, 'org-iam-role'
        ) as client:
            new_manifest = manifest_utils.expand_manifest(manifest, client)
    click.echo('Expanded')
    new_name = f.name.replace(".yaml", '-expanded.yaml')
    logger.info('Writing new manifest: {}'.format(new_name))
    with open(new_name, 'w') as output:
        output.write(
            yaml.safe_dump(new_manifest, default_flow_style=False)
        )


def validate(f):
    logger.info('Validating {}'.format(f.name))
    c = Core(
        source_file=f.name,
        schema_files=[asset_helpers.resolve_from_site_packages('schema.yaml')],
        extensions=[asset_helpers.resolve_from_site_packages('puppet_schema_extensions.py')]
    )
    c.validate(raise_exception=True)
    click.echo("Finished validating: {}".format(f.name))
    click.echo("Finished validating: OK")


def version():
    click.echo("cli version: {}".format(pkg_resources.require("aws-service-catalog-puppet")[0].version))
    with betterboto_client.ClientContextManager('ssm') as ssm:
        response = ssm.get_parameter(
            Name="service-catalog-puppet-regional-version"
        )
        click.echo(
            "regional stack version: {} for region: {}".format(
                response.get('Parameter').get('Value'),
                response.get('Parameter').get('ARN').split(':')[3]
            )
        )
        response = ssm.get_parameter(
            Name="service-catalog-puppet-version"
        )
        click.echo(
            "stack version: {}".format(
                response.get('Parameter').get('Value'),
            )
        )


def upload_config(config):
    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME,
            Type='String',
            Value=yaml.safe_dump(config),
            Overwrite=True,
        )
    click.echo("Uploaded config")


def set_org_iam_role_arn(org_iam_role_arn):
    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN,
            Type='String',
            Value=org_iam_role_arn,
            Overwrite=True,
        )
    click.echo("Uploaded config")


def bootstrap_org_master(puppet_account_id):
    with betterboto_client.ClientContextManager(
            'cloudformation',
    ) as cloudformation:
        org_iam_role_arn = None
        puppet_version = config.get_puppet_version()
        logger.info('Starting bootstrap of org master')
        stack_name = f"{constants.BOOTSTRAP_STACK_NAME}-org-master-{puppet_account_id}"
        template = asset_helpers.read_from_site_packages(f'{constants.BOOTSTRAP_STACK_NAME}-org-master.template.yaml')
        template = Template(template).render(VERSION=puppet_version, puppet_account_id=puppet_account_id)
        args = {
            'StackName': stack_name,
            'TemplateBody': template,
            'Capabilities': ['CAPABILITY_NAMED_IAM'],
            'Parameters': [
                {
                    'ParameterKey': 'PuppetAccountId',
                    'ParameterValue': str(puppet_account_id),
                }, {
                    'ParameterKey': 'Version',
                    'ParameterValue': puppet_version,
                    'UsePreviousValue': False,
                },
            ],
            'Tags': [
                {
                    "Key": "ServiceCatalogPuppet:Actor",
                    "Value": "Framework",
                }
            ]
        }
        cloudformation.create_or_update(**args)
        response = cloudformation.describe_stacks(StackName=stack_name)
        if len(response.get('Stacks')) != 1:
            raise Exception("Expected there to be only one {} stack".format(stack_name))
        stack = response.get('Stacks')[0]

        for output in stack.get('Outputs'):
            if output.get('OutputKey') == constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN:
                logger.info('Finished bootstrap of org-master')
                org_iam_role_arn = output.get("OutputValue")

        if org_iam_role_arn is None:
            raise Exception(
                "Could not find output: {} in stack: {}".format(constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN, stack_name)
            )

    click.echo("Bootstrapped org master, org-iam-role-arn: {}".format(org_iam_role_arn))


def run(what, tail):
    pipelines = {
        'puppet': constants.PIPELINE_NAME
    }
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
        if 'empty.template.yaml' == file.name:
            continue
        template_contents = Template(open(file, 'r').read()).render()
        template = cfn_tools.load_yaml(template_contents)
        click.echo(f"## Resources for stack: {file.name.split('.')[0]}")
        table_data = [
            ['Logical Name', 'Resource Type', 'Name', ],
        ]
        table = terminaltables.AsciiTable(table_data)
        for logical_name, resource in template.get('Resources').items():
            resource_type = resource.get('Type')
            name = '-'
            type_to_name = {
                'AWS::IAM::Role': 'RoleName',
                'AWS::SSM::Parameter': 'Name',
                'AWS::S3::Bucket': 'BucketName',
                'AWS::CodePipeline::Pipeline': 'Name',
                'AWS::CodeBuild::Project': 'Name',
                'AWS::CodeCommit::Repository': 'RepositoryName',
                'AWS::SNS::Topic': 'TopicName',
                'AWS::SQS::Queue': 'QueueName',
            }

            if type_to_name.get(resource_type) is not None:
                name = resource.get('Properties', {}).get(type_to_name.get(resource_type), 'Not Specified')
                if not isinstance(name, str):
                    name = cfn_tools.dump_yaml(name)

            table_data.append([logical_name, resource_type, name])

        click.echo(table.table)
    click.echo(f"n.b. AWS::StackName evaluates to {constants.BOOTSTRAP_STACK_NAME}")


def import_product_set(f, name, portfolio_name):
    url = f"https://raw.githubusercontent.com/awslabs/aws-service-catalog-products/master/{name}/manifest.yaml"
    response = requests.get(url)
    logger.info(
        f"Getting {url}"
    )
    manifest = yaml.safe_load(f.read())
    if manifest.get('launches') is None:
        manifest['launches'] = {}
    manifest_segment = yaml.safe_load(response.text)
    for launch_name, details in manifest_segment.get('launches').items():
        details['portfolio'] = portfolio_name
        manifest['launches'][launch_name] = details
    with open(f.name, 'w') as f:
        f.write(
            yaml.safe_dump(manifest)
        )


def get_manifest():
    with betterboto_client.ClientContextManager('codecommit') as codecommit:
        content = codecommit.get_file(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            filePath="manifest.yaml",
        ).get('fileContent')
        return yaml.safe_load(content)


def save_manifest(manifest):
    with betterboto_client.ClientContextManager('codecommit') as codecommit:
        parent_commit_id = codecommit.get_branch(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            branchName='master',
        ).get('branch').get('commitId')
        codecommit.put_file(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            branchName='master',
            fileContent=yaml.safe_dump(manifest),
            parentCommitId=parent_commit_id,
            commitMessage="Auto generated commit",
            filePath=f"manifest.yaml",
        )


def add_to_accounts(account_or_ou):
    manifest = get_manifest()
    manifest.get('accounts').append(account_or_ou)
    save_manifest(manifest)


def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    manifest = get_manifest()
    for account in manifest.get('accounts', []):
        if account.get('account_id', '') == account_id_or_ou_id_or_ou_path:
            manifest.get('accounts').remove(account)
            return save_manifest(manifest)
        elif account.get('ou', '') == account_id_or_ou_id_or_ou_path:
            manifest.get('accounts').remove(account)
            return save_manifest(manifest)
    raise Exception(f"Did not remove {account_id_or_ou_id_or_ou_path}")


def add_to_launches(launch_name, launch):
    manifest = get_manifest()
    launches = manifest.get('launches', {})
    launches[launch_name] = launch
    manifest['launches'] = launches
    save_manifest(manifest)


def remove_from_launches(launch_name):
    manifest = get_manifest()
    del manifest.get('launches')[launch_name]
    save_manifest(manifest)


def set_config_value(name, value):
    with betterboto_client.ClientContextManager('ssm', region_name=constants.HOME_REGION) as ssm:
        try:
            response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
            config = yaml.safe_load(response.get('Parameter').get('Value'))
        except ssm.exceptions.ParameterNotFound:
            config = {}

        if name == "regions":
            config['regions'] = value if len(value) > 1 else value[0].split(",")
        else:
            config[name] = value.upper() == 'TRUE'

        upload_config(config)


def bootstrap_spokes_in_ou(ou_path_or_id, role_name, iam_role_arns, permission_boundary, num_workers=10):
    org_iam_role_arn = config.get_org_iam_role_arn()
    puppet_account_id = config.get_puppet_account_id()
    if org_iam_role_arn is None:
        click.echo('No org role set - not expanding')
    else:
        click.echo('Expanding using role: {}'.format(org_iam_role_arn))
        with betterboto_client.CrossAccountClientContextManager(
                'organizations', org_iam_role_arn, 'org-iam-role'
        ) as client:
            tasks = []
            if ou_path_or_id.startswith('/'):
                ou_id = client.convert_path_to_ou(ou_path_or_id)
            else:
                ou_id = ou_path_or_id
            logging.info(f"ou_id is {ou_id}")
            response = client.list_children_nested(ParentId=ou_id, ChildType='ACCOUNT')
            for spoke in response:
                tasks.append(
                    management_tasks.BootstrapSpokeAsTask(
                        puppet_account_id=puppet_account_id,
                        account_id=spoke.get('Id'),
                        iam_role_arns=iam_role_arns,
                        role_name=role_name,
                        permission_boundary=permission_boundary,
                    )
                )

        runner.run_tasks_for_bootstrap_spokes_in_ou(tasks, num_workers)


def handle_action_execution_detail(action_execution_detail):
    action_type_id = action_execution_detail.get('input').get('actionTypeId')
    if action_type_id.get('category') == "Build" and action_type_id.get('owner') == "AWS" and action_type_id.get(
            'provider') == "CodeBuild":
        external_execution_id = action_execution_detail.get('output').get('executionResult').get('externalExecutionId')

        with betterboto_client.ClientContextManager(
                "codebuild",
                region_name=config.get_home_region()
        ) as codebuild:
            builds = codebuild.batch_get_builds(ids=[external_execution_id]).get('builds')
            build = builds[0]
            log_details = build.get('logs')
            with betterboto_client.ClientContextManager(
                    "logs",
                    region_name=config.get_home_region()
            ) as logs:
                with open(
                        f"log-{action_execution_detail.get('input').get('configuration').get('ProjectName')}.log", 'w'
                ) as f:
                    params = {
                        'logGroupName': log_details.get('groupName'),
                        'logStreamName': log_details.get('streamName'),
                        'startFromHead': True,
                    }
                    has_more_logs = True
                    while has_more_logs:
                        get_log_events_response = logs.get_log_events(**params)
                        if (len(get_log_events_response.get('events'))) > 0:
                            params['nextToken'] = get_log_events_response.get('nextForwardToken')
                        else:
                            has_more_logs = False
                            if params.get('nextToken'):
                                del params['nextToken']
                        for e in get_log_events_response.get('events'):
                            d = datetime.utcfromtimestamp(e.get('timestamp') / 1000).strftime('%Y-%m-%d %H:%M:%S')
                            f.write(
                                f"{d} : {e.get('message')}"
                            )


def export_puppet_pipeline_logs(execution_id):
    with betterboto_client.ClientContextManager(
            "codepipeline",
            region_name=config.get_home_region()
    ) as codepipeline:
        action_execution_details = codepipeline.list_action_executions(
            pipelineName=constants.PIPELINE_NAME,
            filter={
                'pipelineExecutionId': execution_id
            },
        ).get('actionExecutionDetails')

        for action_execution_detail in action_execution_details:
            handle_action_execution_detail(action_execution_detail)


def uninstall():
    with betterboto_client.ClientContextManager(
            "cloudformation",
            region_name=config.get_home_region()
    ) as cloudformation:
        cloudformation.ensure_deleted(StackName=constants.BOOTSTRAP_STACK_NAME)


def release_spoke():
    with betterboto_client.ClientContextManager(
            "cloudformation",
            region_name=config.get_home_region()
    ) as cloudformation:
        cloudformation.ensure_deleted(StackName=f"{constants.BOOTSTRAP_STACK_NAME}-spoke")
