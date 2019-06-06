# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from colorclass import Color
from terminaltables import AsciiTable

import copy

import shutil
import json

import luigi
import pkg_resources
import yaml
import logging
import os
import click

from jinja2 import Template
from pykwalify.core import Core
from betterboto import client as betterboto_client


from servicecatalog_puppet import luigi_tasks_and_targets
from servicecatalog_puppet import cli_command_helpers
from servicecatalog_puppet import aws
from servicecatalog_puppet import manifest_utils


from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import constants

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DISALLOWED_ATTRIBUTES_FOR_TERMINATED_LAUNCHES = [
    'depends_on',
    'outputs',
    'parameters',
]


def cli(info, info_line_numbers):
    """cli for pipeline tools"""
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

    manifest = manifest_utils.load(f)
    deployment_map = manifest_utils.build_deployment_map(manifest)
    cli_command_helpers.create_share_template(deployment_map, cli_command_helpers.get_puppet_account_id())


def deploy(f, single_account):
    manifest = manifest_utils.load(f)
    deployment_map = manifest_utils.build_deployment_map(manifest)
    deployment_map = cli_command_helpers.set_regions_for_deployment_map(deployment_map)

    all_tasks = {}
    tasks_to_run = []
    puppet_account_id = cli_command_helpers.get_puppet_account_id()

    for account_id, deployments_for_account in deployment_map.items():
        for launch_name, launch_details in deployments_for_account.get('launches').items():
            for region_name, regional_details in launch_details.get('regional_details').items():
                product_id = regional_details.get('product_id')
                required_parameters = {}

                role = f"arn:aws:iam::{account_id}:role/servicecatalog-puppet/PuppetRole"
                with betterboto_client.CrossAccountClientContextManager(
                        'servicecatalog', role, f'sc-{account_id}-{region_name}', region_name=region_name
                ) as service_catalog:
                    response = service_catalog.describe_provisioning_parameters(
                        ProductId=product_id,
                        ProvisioningArtifactId=regional_details.get('version_id'),
                        PathId=aws.get_path_for_product(service_catalog, product_id),
                    )
                    for provisioning_artifact_parameters in response.get('ProvisioningArtifactParameters', []):
                        parameter_key = provisioning_artifact_parameters.get('ParameterKey')
                        required_parameters[parameter_key] = True

                    regular_parameters, ssm_parameters = cli_command_helpers.get_parameters_for_launch(
                        required_parameters,
                        deployment_map,
                        manifest,
                        launch_details,
                        account_id,
                        launch_details.get('status', constants.PROVISIONED),
                    )

                logger.info(f"Found a new launch: {launch_name}")

                task = {
                    'launch_name': launch_name,
                    'portfolio': launch_details.get('portfolio'),
                    'product': launch_details.get('product'),
                    'version': launch_details.get('version'),

                    'product_id': regional_details.get('product_id'),
                    'version_id': regional_details.get('version_id'),

                    'account_id': account_id,
                    'region': region_name,
                    'puppet_account_id': puppet_account_id,

                    'parameters': regular_parameters,
                    'ssm_param_inputs': ssm_parameters,

                    'depends_on': launch_details.get('depends_on', []),

                    "status": launch_details.get('status', constants.PROVISIONED),

                    'dependencies': [],
                }

                if manifest.get('configuration'):
                    if manifest.get('configuration').get('retry_count'):
                        task['retry_count'] = manifest.get('configuration').get('retry_count')

                if launch_details.get('configuration'):
                    if launch_details.get('configuration').get('retry_count'):
                        task['retry_count'] = launch_details.get('configuration').get('retry_count')

                for output in launch_details.get('outputs', {}).get('ssm', []):
                    t = copy.deepcopy(task)
                    del t['depends_on']
                    tasks_to_run.append(
                        luigi_tasks_and_targets.SetSSMParamFromProvisionProductTask(**output, dependency=t)
                    )

                all_tasks[f"{task.get('account_id')}-{task.get('region')}-{task.get('launch_name')}"] = task

    logger.info(f"Deployment plan: {json.dumps(all_tasks)}")

    for task in cli_command_helpers.wire_dependencies(all_tasks):
        task_status = task.get('status')
        del task['status']
        if task_status == constants.PROVISIONED:
            tasks_to_run.append(luigi_tasks_and_targets.ProvisionProductTask(**task))
        elif task_status == constants.TERMINATED:
            for attribute in DISALLOWED_ATTRIBUTES_FOR_TERMINATED_LAUNCHES:
                logger.info(f"checking {launch_name} for disallowed attributes")
                attribute_value = task.get(attribute)
                if attribute_value is not None:
                    if isinstance(attribute_value, list):
                        if len(attribute_value) != 0:
                            raise Exception(f"Launch {task.get('launch_name')} has disallowed attribute: {attribute}")
                    elif isinstance(attribute_value, dict):
                        if len(attribute_value.keys()) != 0:
                            raise Exception(f"Launch {task.get('launch_name')} has disallowed attribute: {attribute}")
                    else:
                        raise Exception(f"Launch {task.get('launch_name')} has disallowed attribute: {attribute}")

            for a in ['parameters', 'ssm_param_inputs', 'outputs', 'dependencies']:
                if task.get(a, None) is not None:
                    del task[a]
            tasks_to_run.append(luigi_tasks_and_targets.TerminateProductTask(**task))
        else:
            raise Exception(f"Unsupported status of {task_status}")

    luigi.build(
        tasks_to_run,
        local_scheduler=True,
        detailed_summary=True,
        workers=10,
        log_level='INFO',
    )


def bootstrap_spoke_as(puppet_account_id, iam_role_arns):
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
        cli_command_helpers._do_bootstrap_spoke(puppet_account_id, cloudformation, cli_command_helpers.get_puppet_version())


def bootstrap_spoke(puppet_account_id):
    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        cli_command_helpers._do_bootstrap_spoke(puppet_account_id, cloudformation, cli_command_helpers.get_puppet_version())


def bootstrap_branch(branch_name):
    cli_command_helpers._do_bootstrap("https://github.com/awslabs/aws-service-catalog-puppet/archive/{}.zip".format(branch_name))


def bootstrap():
    cli_command_helpers._do_bootstrap(cli_command_helpers.get_puppet_version())


def seed(complexity, p):
    example = "manifest-{}.yaml".format(complexity)
    shutil.copy2(
        asset_helpers.resolve_from_site_packages(
            os.path.sep.join(['manifests', example])
        ),
        os.path.sep.join([p, "manifest.yaml"])
    )


def list_launches(f):
    manifest = manifest_utils.load(f)
    click.echo("Getting details from your account...")
    ALL_REGIONS = cli_command_helpers.get_regions(os.environ.get("AWS_DEFAULT_REGION"))
    deployment_map = manifest_utils.build_deployment_map(manifest)
    account_ids = [a.get('account_id') for a in manifest.get('accounts')]
    deployments = {}
    for account_id in account_ids:
        for region_name in ALL_REGIONS:
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
                                deployments[account_id] = {'account_id': account_id, 'launches': {}}

                            if deployments[account_id]['launches'].get(launch_name) is None:
                                deployments[account_id]['launches'][launch_name] = {}

                            deployments[account_id]['launches'][launch_name][region_name] = {
                                'launch_name': launch_name,
                                'portfolio': portfolio.get('DisplayName'),
                                'product': manifest.get('launches', {}).get(launch_name, {}).get('product'),
                                'version': provisioning_artifact_response.get('Name'),
                                'active': provisioning_artifact_response.get('Active'),
                                'region': region_name,
                                'status': status,
                            }
                            output_path = os.path.sep.join([
                                constants.LAUNCHES,
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

    table = [
        ['account_id', 'region', 'launch', 'portfolio', 'product', 'expected_version', 'actual_version', 'active',
         'status']
    ]
    for account_id, details in deployment_map.items():
        for launch_name, launch in details.get('launches', {}).items():
            if deployments.get(account_id, {}).get('launches', {}).get(launch_name) is None:
                pass
            else:
                for region, regional_details in deployments[account_id]['launches'][launch_name].items():
                    if regional_details.get('status') == "AVAILABLE":
                        status = Color("{green}" + regional_details.get('status') + "{/green}")
                    else:
                        status = Color("{red}" + regional_details.get('status') + "{/red}")
                    expected_version = launch.get('version')
                    actual_version = regional_details.get('version')
                    if expected_version == actual_version:
                        actual_version = Color("{green}" + actual_version + "{/green}")
                    else:
                        actual_version = Color("{red}" + actual_version + "{/red}")
                    active = regional_details.get('active')
                    if active:
                        active = Color("{green}" + str(active) + "{/green}")
                    else:
                        active = Color("{orange}" + str(active) + "{/orange}")
                    table.append([
                        account_id,
                        region,
                        launch_name,
                        regional_details.get('portfolio'),
                        regional_details.get('product'),
                        expected_version,
                        actual_version,
                        active,
                        status,
                    ])
    click.echo(AsciiTable(table).table)


def expand(f):
    click.echo('Expanding')
    manifest = manifest_utils.load(f)
    org_iam_role_arn = cli_command_helpers.get_org_iam_role_arn()
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
    c = Core(source_file=f.name, schema_files=[asset_helpers.resolve_from_site_packages('schema.yaml')])
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


def upload_config(p):
    content = open(p, 'r').read()
    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME,
            Type='String',
            Value=content,
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
        org_iam_role_arn = cli_command_helpers._do_bootstrap_org_master(
            puppet_account_id, cloudformation, cli_command_helpers.get_puppet_version()
        )
    click.echo("Bootstrapped org master, org-iam-role-arn: {}".format(org_iam_role_arn))


def quick_start():
    click.echo("Quick Start running...")
    puppet_version = cli_command_helpers.get_puppet_version()
    with betterboto_client.ClientContextManager('sts') as sts:
        puppet_account_id = sts.get_caller_identity().get('Account')
        click.echo("Going to use puppet_account_id: {}".format(puppet_account_id))
    click.echo("Bootstrapping account as a spoke")
    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        cli_command_helpers._do_bootstrap_spoke(puppet_account_id, cloudformation, puppet_version)

    click.echo("Setting the config")
    content = yaml.safe_dump({
        "regions": [
            'eu-west-1',
            'eu-west-2',
            'eu-west-3'
        ]
    })
    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME,
            Type='String',
            Value=content,
            Overwrite=True,
        )
        click.echo("Bootstrapping account as the master")
        org_iam_role_arn = cli_command_helpers._do_bootstrap_org_master(
            puppet_account_id, cloudformation, puppet_version
        )
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN,
            Type='String',
            Value=org_iam_role_arn,
            Overwrite=True,
        )
    click.echo("Bootstrapping the account now!")
    cli_command_helpers._do_bootstrap(puppet_version)

    if os.path.exists('ServiceCatalogPuppet'):
        click.echo("Found ServiceCatalogPuppet so not cloning or seeding")
    else:
        click.echo("Cloning for you")
        command = "git clone " \
                  "--config 'credential.helper=!aws codecommit credential-helper $@' " \
                  "--config 'credential.UseHttpPath=true' " \
                  "https://git-codecommit.{}.amazonaws.com/v1/repos/ServiceCatalogPuppet".format(
            os.environ.get("AWS_DEFAULT_REGION")
        )
        os.system(command)
        click.echo("Seeding")
        manifest = Template(
            asset_helpers.read_from_site_packages(os.path.sep.join(["manifests", "manifest-quickstart.yaml"]))
        ).render(
            ACCOUNT_ID=puppet_account_id
        )
        open(os.path.sep.join(["ServiceCatalogPuppet", "manifest.yaml"]), 'w').write(
            manifest
        )
        click.echo("Pushing manifest")
        os.system("cd ServiceCatalogPuppet && git add manifest.yaml && git commit -am 'initial add' && git push")

    click.echo("All done!")


