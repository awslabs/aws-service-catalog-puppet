# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import shutil

import click
import pkg_resources
import yaml
import logging
import os
from pykwalify.core import Core

from betterboto import client as betterboto_client

from servicecatalog_puppet.commands.list_launches import do_list_launches
from servicecatalog_puppet.utils import manifest as manifest_utils
from servicecatalog_puppet.asset_helpers import resolve_from_site_packages
from servicecatalog_puppet.constants import CONFIG_PARAM_NAME, CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN
from servicecatalog_puppet.core import get_org_iam_role_arn, write_templates, create_share_template, \
    deploy_launches
from servicecatalog_puppet.commands.bootstrap import do_bootstrap
from servicecatalog_puppet.commands.bootstrap_spoke import do_bootstrap_spoke
from servicecatalog_puppet.commands.expand import do_expand
from servicecatalog_puppet.utils.manifest import build_deployment_map
from servicecatalog_puppet.commands.bootstrap_org_master import do_bootstrap_org_master

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


def get_puppet_account_id():
    with betterboto_client.ClientContextManager('sts') as sts:
        return sts.get_caller_identity().get('Account')


@cli.command()
@click.argument('f', type=click.File())
def generate_shares(f):
    logger.info('Starting to generate shares for: {}'.format(f.name))

    manifest = manifest_utils.load(f)
    deployment_map = build_deployment_map(manifest)
    create_share_template(deployment_map, get_puppet_account_id())


@cli.command()
@click.argument('f', type=click.File())
@click.option('--single-account', default=None)
def deploy(f, single_account):
    manifest = manifest_utils.load(f)
    deployment_map = build_deployment_map(manifest)
    write_templates(deployment_map)
    logger.info('Starting to deploy')
    deploy_launches(
        deployment_map,
        manifest.get('parameters', {}),
        single_account,
        get_puppet_account_id()
    )
    logger.info('Finished deploy')


@cli.command()
@click.argument('puppet_account_id')
@click.argument('iam_role_arns', nargs=-1)
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
    manifest = manifest_utils.load(f)
    do_list_launches(manifest)


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


@cli.command()
@click.argument('puppet_account_id')
def bootstrap_org_master(puppet_account_id):
    with betterboto_client.ClientContextManager(
        'cloudformation',
    ) as cloudformation:
        org_iam_role_arn = do_bootstrap_org_master(
            puppet_account_id, cloudformation, get_puppet_version()
        )
    click.echo("Bootstrapped org master, org-iam-role-arn: {}".format(org_iam_role_arn))


if __name__ == "__main__":
    cli()
