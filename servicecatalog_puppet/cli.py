# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
import shutil

import click
import pkg_resources
import yaml
import logging
import os
from pykwalify.core import Core

from betterboto import client as betterboto_client
from terminaltables import AsciiTable
from colorclass import Color

from servicecatalog_puppet.utils import manifest as manifest_utils
from servicecatalog_puppet.asset_helpers import resolve_from_site_packages
from servicecatalog_puppet.constants import LAUNCHES, HOME_REGION, \
    CONFIG_PARAM_NAME, CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN
from servicecatalog_puppet.core import get_regions, get_org_iam_role_arn, write_templates, create_share_template, \
    deploy_launches
from servicecatalog_puppet.commands.bootstrap import do_bootstrap
from servicecatalog_puppet.commands.bootstrap_spoke import do_bootstrap_spoke
from servicecatalog_puppet.commands.expand import do_expand
from servicecatalog_puppet.utils.manifest import build_deployment_map

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@click.group()
@click.option('--info/--no-info', default=False)
@click.option('--info-line-numbers/--no-info-line-numbers', default=False)
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


@cli.command()
@click.argument('f', type=click.File())
def generate_shares(f):
    logger.info('Starting to generate shares for: {}'.format(f.name))

    manifest = manifest_utils.load(f)
    deployment_map = build_deployment_map(manifest)
    create_share_template(deployment_map)


@cli.command()
@click.argument('f', type=click.File())
@click.option('--single-account', default=None)
def deploy(f, single_account):
    manifest = manifest_utils.load(f)
    deployment_map = build_deployment_map(manifest)
    write_templates(deployment_map)
    logger.info('Starting to deploy')
    with betterboto_client.ClientContextManager('sts') as sts:
        puppet_account_id = sts.get_caller_identity().get('Account')
    deploy_launches(
        deployment_map,
        manifest.get('parameters', {}),
        single_account,
        puppet_account_id
    )
    logger.info('Finished deploy')


@cli.command()
@click.argument('puppet_account_id')
@click.argument('iam_role_arn')
def bootstrap_spoke_as(puppet_account_id, iam_role_arn):
    with betterboto_client.CrossAccountClientContextManager('cloudformation', iam_role_arn,
                                                            'bootstrapping') as cloudformation:
        do_bootstrap_spoke(puppet_account_id, cloudformation, get_puppet_version())


@cli.command()
@click.argument('puppet_account_id')
def bootstrap_spoke(puppet_account_id):
    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        do_bootstrap_spoke(puppet_account_id, cloudformation, get_puppet_version())


@cli.command()
@click.argument('branch-name')
def bootstrap_branch(branch_name):
    do_bootstrap("https://github.com/awslabs/aws-service-catalog-puppet/archive/{}.zip".format(branch_name))


def get_puppet_version():
    return pkg_resources.require("aws-service-catalog-puppet")[0].version


@cli.command()
def bootstrap():
    do_bootstrap(get_puppet_version())


@cli.command()
@click.argument('complexity', default='simple')
@click.argument('p', type=click.Path(exists=True))
def seed(complexity, p):
    example = "manifest-{}.yaml".format(complexity)
    shutil.copy2(
        resolve_from_site_packages(
            os.path.sep.join(['manifests', example])
        ),
        os.path.sep.join([p, "manifest.yaml"])
    )


@cli.command()
@click.argument('f', type=click.File())
def list_launches(f):
    click.echo("Getting details from your account...")
    ALL_REGIONS = get_regions()
    manifest = manifest_utils.load(f)
    deployment_map = build_deployment_map(manifest)

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
                for portfolio in response.get('PortfolioDetails', []):
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
                                'product': manifest.get('launches').get(launch_name).get('product'),
                                'version': provisioning_artifact_response.get('Name'),
                                'active': provisioning_artifact_response.get('Active'),
                                'region': region_name,
                                'status': status,
                            }
                            output_path = os.path.sep.join([
                                LAUNCHES,
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
        for launch_name, launch in details.get('launches').items():
            if deployments.get(account_id).get('launches').get(launch_name) is None:
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


@cli.command()
@click.argument('f', type=click.File())
def expand(f):
    click.echo('Expanding')
    manifest = manifest_utils.load(f)
    org_iam_role_arn = get_org_iam_role_arn()
    if org_iam_role_arn is None:
        click.echo('No org role set - not expanding')
        new_manifest = manifest
    else:
        click.echo('Expanding using role: {}'.format(org_iam_role_arn))
        with betterboto_client.CrossAccountClientContextManager(
                'organizations', org_iam_role_arn, 'org-iam-role'
        ) as client:
            new_manifest = do_expand(manifest, client)
    click.echo('Expanded')
    new_name = f.name.replace(".yaml", '-expanded.yaml')
    logger.info('Writing new manifest: {}'.format(new_name))
    with open(new_name, 'w') as output:
        output.write(
            yaml.safe_dump(new_manifest, default_flow_style=False)
        )


@cli.command()
@click.argument('f', type=click.File())
def validate(f):
    logger.info('Validating {}'.format(f.name))
    c = Core(source_file=f.name, schema_files=[resolve_from_site_packages('schema.yaml')])
    c.validate(raise_exception=True)
    click.echo("Finished validating: {}".format(f.name))
    click.echo("Finished validating: OK")


@cli.command()
def version():
    click.echo("cli version: {}".format(pkg_resources.require("aws-service-catalog-puppet")[0].version))
    with betterboto_client.ClientContextManager('ssm', region_name=HOME_REGION) as ssm:
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


@cli.command()
@click.argument('p', type=click.Path(exists=True))
def upload_config(p):
    content = open(p, 'r').read()
    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.put_parameter(
            Name=CONFIG_PARAM_NAME,
            Type='String',
            Value=content,
            Overwrite=True,
        )
    click.echo("Uploaded config")


@cli.command()
@click.argument('org-iam-role-arn')
def set_org_iam_role_arn(org_iam_role_arn):
    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.put_parameter(
            Name=CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN,
            Type='String',
            Value=org_iam_role_arn,
            Overwrite=True,
        )
    click.echo("Uploaded config")


if __name__ == "__main__":
    cli()
