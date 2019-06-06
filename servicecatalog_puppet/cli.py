# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import copy

import shutil
import json

import luigi
import click
import pkg_resources
import yaml
import logging
import os

from jinja2 import Template
from pykwalify.core import Core
from betterboto import client as betterboto_client

from servicecatalog_puppet import aws
from servicecatalog_puppet.luigi_tasks_and_targets import ProvisionProductTask, SetSSMParamFromProvisionProductTask, \
    TerminateProductTask
from servicecatalog_puppet.commands.list_launches import do_list_launches
from servicecatalog_puppet.utils import manifest as manifest_utils
from servicecatalog_puppet.asset_helpers import resolve_from_site_packages, read_from_site_packages
from servicecatalog_puppet.constants import CONFIG_PARAM_NAME, CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN
from servicecatalog_puppet.core import get_org_iam_role_arn, create_share_template, \
    get_regions, get_provisioning_artifact_id_for
from servicecatalog_puppet.commands.bootstrap import do_bootstrap
from servicecatalog_puppet.commands.bootstrap_spoke import do_bootstrap_spoke
from servicecatalog_puppet.commands.expand import do_expand
from servicecatalog_puppet.utils.manifest import build_deployment_map
from servicecatalog_puppet.commands.bootstrap_org_master import do_bootstrap_org_master

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PROVISIONED = 'provisioned'
TERMINATED = 'terminated'

DISALLOWED_ATTRIBUTES_FOR_TERMINATED_LAUNCHES = [
    'depends_on',
    'outputs',
    'parameters',
]


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


def set_regions_for_deployment_map(deployment_map):
    logger.info('Starting to write the templates')
    ALL_REGIONS = get_regions()
    for account_id, account_details in deployment_map.items():
        for launch_name, launch_details in account_details.get('launches').items():
            logger.info('Looking at account: {} and launch: {}'.format(account_id, launch_name))
            if launch_details.get('match') == 'account_match':
                logger.info('Setting regions for account matched')
                for a in launch_details.get('deploy_to').get('accounts'):
                    if a.get('account_id') == account_id:
                        regions = a.get('regions')
                        if regions == "enabled":
                            regions = account_details.get('regions_enabled')
                        elif regions == "default_region" or regions is None:
                            regions = account_details.get('default_region')
                        elif regions == "all":
                            regions = ALL_REGIONS
                        elif isinstance(regions, list):
                            for region in regions:
                                if region not in ALL_REGIONS:
                                    raise Exception("Unknown region: {}".format(region))
                        elif isinstance(regions, str) and regions in ALL_REGIONS:
                            pass
                        else:
                            raise Exception("Unknown regions: {}".format(regions))
                        if isinstance(regions, str):
                            regions = [regions]
                        launch_details['regions'] = regions

            elif launch_details.get('match') == 'tag_match':
                logger.info('Setting regions for tag matched')
                for t in launch_details.get('deploy_to').get('tags'):
                    if t.get('tag') in account_details.get('tags'):
                        regions = t.get('regions')
                        if regions == "enabled":
                            regions = account_details.get('regions_enabled')
                        elif regions == "default_region" or regions is None:
                            regions = account_details.get('default_region')
                        elif regions == "all":
                            regions = ALL_REGIONS
                        elif isinstance(regions, list):
                            for region in regions:
                                if region not in ALL_REGIONS:
                                    raise Exception("Unknown region: {}".format(region))
                        elif isinstance(regions, str) and regions in ALL_REGIONS:
                            pass
                        else:
                            raise Exception("Unknown regions: {}".format(regions))
                        if isinstance(regions, str):
                            regions = [regions]
                        launch_details['regions'] = regions

            assert launch_details.get('regions') is not None, "Launch {} has no regions set".format(launch_name)
            launch_details['regional_details'] = {}
            for region in launch_details.get('regions'):
                logger.info('Starting region: {}'.format(region))
                product_id, version_id = get_provisioning_artifact_id_for(
                    launch_details.get('portfolio'),
                    launch_details.get('product'),
                    launch_details.get('version'),
                    account_id,
                    region
                )
                launch_details['regional_details'][region] = {
                    'product_id': product_id,
                    'version_id': version_id,
                }
    return deployment_map


def get_parameters_for_launch(required_parameters, deployment_map, manifest, launch_details, account_id, status):
    regular_parameters = []
    ssm_parameters = []

    for required_parameter_name in required_parameters.keys():
        account_ssm_param = deployment_map.get(account_id).get('parameters', {}).get(required_parameter_name, {}).get('ssm')
        account_regular_param = deployment_map.get(account_id).get('parameters', {}).get(required_parameter_name, {}).get('default')

        launch_params = launch_details.get('parameters', {})
        launch_ssm_param = launch_params.get(required_parameter_name, {}).get('ssm')
        launch_regular_param = launch_params.get(required_parameter_name, {}).get('default')

        manifest_params = manifest.get('parameters', {})
        manifest_ssm_param = manifest_params.get(required_parameter_name, {}).get('ssm')
        manifest_regular_param = manifest_params.get(required_parameter_name, {}).get('default')

        if status == PROVISIONED and account_ssm_param:
            ssm_parameters.append(
                get_ssm_config_for_parameter(account_ssm_param, required_parameter_name)
            )
        elif status == PROVISIONED and account_regular_param:
            regular_parameters.append({
                'name': required_parameter_name,
                'value': str(account_regular_param),
            })

        elif launch_ssm_param:
            ssm_parameters.append(
                get_ssm_config_for_parameter(launch_ssm_param, required_parameter_name)
            )
        elif launch_regular_param:
            regular_parameters.append({
                'name': required_parameter_name,
                'value': launch_regular_param,
            })

        elif status == PROVISIONED and manifest_ssm_param:
            ssm_parameters.append(
                get_ssm_config_for_parameter(manifest_ssm_param, required_parameter_name)
            )
        elif status == PROVISIONED and manifest_regular_param:
            regular_parameters.append({
                'name': required_parameter_name,
                'value': manifest_regular_param,
            })

    return regular_parameters, ssm_parameters


def get_ssm_config_for_parameter(account_ssm_param, required_parameter_name):
    if account_ssm_param.get('region') is not None:
        return {
            'name': account_ssm_param.get('name'),
            'region': account_ssm_param.get('region'),
            'parameter_name': required_parameter_name,
        }
    else:
        return {
            'name': account_ssm_param.get('name'),
            'parameter_name': required_parameter_name,
        }


@cli.command()
@click.argument('f', type=click.File())
@click.option('--single-account', default=None)
def deploy(f, single_account):
    manifest = manifest_utils.load(f)
    deployment_map = build_deployment_map(manifest)
    deployment_map = set_regions_for_deployment_map(deployment_map)

    all_tasks = {}
    tasks_to_run = []
    puppet_account_id = get_puppet_account_id()

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

                    regular_parameters, ssm_parameters = get_parameters_for_launch(
                        required_parameters,
                        deployment_map,
                        manifest,
                        launch_details,
                        account_id,
                        launch_details.get('status', PROVISIONED),
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

                    "status": launch_details.get('status', PROVISIONED),

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
                        SetSSMParamFromProvisionProductTask(**output, dependency=t)
                    )

                all_tasks[f"{task.get('account_id')}-{task.get('region')}-{task.get('launch_name')}"] = task

    logger.info(f"Deployment plan: {json.dumps(all_tasks)}")

    for task in wire_dependencies(all_tasks):
        task_status = task.get('status')
        del task['status']
        if task_status == PROVISIONED:
            tasks_to_run.append(ProvisionProductTask(**task))
        elif task_status == TERMINATED:
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
            tasks_to_run.append(TerminateProductTask(**task))
        else:
            raise Exception(f"Unsupported status of {task_status}")

    luigi.build(
        tasks_to_run,
        local_scheduler=True,
        detailed_summary=True,
        workers=10,
        log_level='INFO',
    )


def wire_dependencies(all_tasks):
    tasks_to_run = []
    for task_uid, task in all_tasks.items():
        for dependency in task.get('depends_on', []):
            for task_uid_2, task_2 in all_tasks.items():
                if task_2.get('launch_name') == dependency:
                    task.get('dependencies').append(task_2)
        del task['depends_on']
        logger.info(f"Scheduling ProvisionProductTask: {json.dumps(task)}")
        tasks_to_run.append(task)
    return tasks_to_run


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


@cli.command()
def quick_start():
    click.echo("Quick Start running...")
    puppet_version = get_puppet_version()
    with betterboto_client.ClientContextManager('sts') as sts:
        puppet_account_id = sts.get_caller_identity().get('Account')
        click.echo("Going to use puppet_account_id: {}".format(puppet_account_id))
    click.echo("Bootstrapping account as a spoke")
    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        do_bootstrap_spoke(puppet_account_id, cloudformation, puppet_version)

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
            Name=CONFIG_PARAM_NAME,
            Type='String',
            Value=content,
            Overwrite=True,
        )
        click.echo("Bootstrapping account as the master")
        org_iam_role_arn = do_bootstrap_org_master(
            puppet_account_id, cloudformation, puppet_version
        )
        ssm.put_parameter(
            Name=CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN,
            Type='String',
            Value=org_iam_role_arn,
            Overwrite=True,
        )
    click.echo("Bootstrapping the account now!")
    do_bootstrap(puppet_version)

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
            read_from_site_packages(os.path.sep.join(["manifests", "manifest-quickstart.yaml"]))
        ).render(
            ACCOUNT_ID=puppet_account_id
        )
        open(os.path.sep.join(["ServiceCatalogPuppet", "manifest.yaml"]), 'w').write(
            manifest
        )
        click.echo("Pushing manifest")
        os.system("cd ServiceCatalogPuppet && git add manifest.yaml && git commit -am 'initial add' && git push")

    click.echo("All done!")


if __name__ == "__main__":
    cli()
