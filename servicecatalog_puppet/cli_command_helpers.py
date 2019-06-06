# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from threading import Thread

import click
import os

from copy import deepcopy

import pkg_resources
import json
from betterboto import client as betterboto_client
from jinja2 import Template

from asset_helpers import read_from_site_packages
from constants import BOOTSTRAP_STACK_NAME, PUPPET_ORG_ROLE_FOR_EXPANDS_ARN, SERVICE_CATALOG_PUPPET_REPO_NAME

import logging

import os
import time
from threading import Thread
import traceback

import yaml
from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

from servicecatalog_puppet.asset_helpers import resolve_from_site_packages
from servicecatalog_puppet.constants import HOME_REGION_PARAM_NAME, CONFIG_PARAM_NAME, CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN, TEMPLATES, PREFIX


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_regions(default_region=None):
    logger.info("getting regions,  default_region: {}".format(default_region))
    with betterboto_client.ClientContextManager(
            'ssm',
            region_name=default_region if default_region else get_home_region()
    ) as ssm:
        response = ssm.get_parameter(Name=CONFIG_PARAM_NAME)
        config = yaml.safe_load(response.get('Parameter').get('Value'))
        return config.get('regions')


def get_home_region():
    with betterboto_client.ClientContextManager('ssm') as ssm:
        response = ssm.get_parameter(Name=HOME_REGION_PARAM_NAME)
        return response.get('Parameter').get('Value')


def get_org_iam_role_arn():
    with betterboto_client.ClientContextManager('ssm', region_name=get_home_region()) as ssm:
        try:
            response = ssm.get_parameter(Name=CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN)
            return yaml.safe_load(response.get('Parameter').get('Value'))
        except ssm.exceptions.ParameterNotFound as e:
            logger.info("No parameter set for: {}".format(CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN))
            return None


def get_provisioning_artifact_id_for(portfolio_name, product_name, version_name, account_id, region):
    logger.info("Getting provisioning artifact id for: {} {} {} in the region: {} of account: {}".format(
        portfolio_name, product_name, version_name, region, account_id
    ))
    role = "arn:aws:iam::{}:role/{}".format(account_id, 'servicecatalog-puppet/PuppetRole')
    with betterboto_client.CrossAccountClientContextManager(
            'servicecatalog', role, "-".join([account_id, region]), region_name=region
    ) as cross_account_servicecatalog:
        product_id = None
        version_id = None
        portfolio_id = None
        args = {}
        while True:
            response = cross_account_servicecatalog.list_accepted_portfolio_shares()
            assert response.get('NextPageToken') is None, "Pagination not supported"
            for portfolio_detail in response.get('PortfolioDetails'):
                if portfolio_detail.get('DisplayName') == portfolio_name:
                    portfolio_id = portfolio_detail.get('Id')
                    break

            if portfolio_id is None:
                response = cross_account_servicecatalog.list_portfolios()
                for portfolio_detail in response.get('PortfolioDetails', []):
                    if portfolio_detail.get('DisplayName') == portfolio_name:
                        portfolio_id = portfolio_detail.get('Id')
                        break

            assert portfolio_id is not None, "Could not find portfolio"
            logger.info("Found portfolio: {}".format(portfolio_id))

            args['PortfolioId'] = portfolio_id
            response = cross_account_servicecatalog.search_products_as_admin(
                **args
            )
            for product_view_details in response.get('ProductViewDetails'):
                product_view = product_view_details.get('ProductViewSummary')
                if product_view.get('Name') == product_name:
                    logger.info('Found product: {}'.format(product_view))
                    product_id = product_view.get('ProductId')
            if response.get('NextPageToken', None) is not None:
                args['PageToken'] = response.get('NextPageToken')
            else:
                break
        assert product_id is not None, "Did not find product looking for"

        response = cross_account_servicecatalog.list_provisioning_artifacts(
            ProductId=product_id
        )
        assert response.get('NextPageToken') is None, "Pagination not support"
        for provisioning_artifact_detail in response.get('ProvisioningArtifactDetails'):
            if provisioning_artifact_detail.get('Name') == version_name:
                version_id = provisioning_artifact_detail.get('Id')
        assert version_id is not None, "Did not find version looking for"
        return product_id, version_id


def generate_bucket_policies_for_shares(deployment_map, puppet_account_id):
    shares = {
        'accounts': [],
        'organizations': [],
    }
    for account_id, deployment in deployment_map.items():
        if account_id == puppet_account_id:
            continue
        if deployment.get('expanded_from') is None:
            if account_id not in shares['accounts']:
                shares['accounts'].append(account_id)
        else:
            if deployment.get('organization') not in shares['organizations']:
                shares['organizations'].append(deployment.get('organization'))
    return shares


def write_share_template(portfolio_use_by_account, region, host_account_id, sharing_policies):
    output = os.path.sep.join([TEMPLATES, 'shares', region])
    if not os.path.exists(output):
        os.makedirs(output)

    with open(os.sep.join([output, "shares.template.yaml"]), 'w') as f:
        f.write(
            env.get_template('shares.template.yaml.j2').render(
                portfolio_use_by_account=portfolio_use_by_account,
                host_account_id=host_account_id,
                HOME_REGION=get_home_region(),
                sharing_policies=sharing_policies,
            )
        )


def create_share_template(deployment_map, puppet_account_id):
    logger.info("deployment_map: {}".format(deployment_map))
    ALL_REGIONS = get_regions()
    for region in ALL_REGIONS:
        logger.info("starting to build shares for region: {}".format(region))
        with betterboto_client.ClientContextManager('servicecatalog', region_name=region) as servicecatalog:
            portfolio_ids = {}
            args = {}
            while True:

                response = servicecatalog.list_portfolios(
                    **args
                )

                for portfolio_detail in response.get('PortfolioDetails'):
                    portfolio_ids[portfolio_detail.get('DisplayName')] = portfolio_detail.get('Id')

                if response.get('PageToken') is not None:
                    args['PageToken'] = response.get('PageToken')
                else:
                    break

            logger.info("Portfolios in use in region: {}".format(portfolio_ids))

            portfolio_use_by_account = {}
            for account_id, launch_details in deployment_map.items():
                if portfolio_use_by_account.get(account_id) is None:
                    portfolio_use_by_account[account_id] = []
                for launch_id, launch in launch_details.get('launches').items():
                    logger.info("portfolio ids: {}".format(portfolio_ids))
                    p = portfolio_ids[launch.get('portfolio')]
                    if p not in portfolio_use_by_account[account_id]:
                        portfolio_use_by_account[account_id].append(p)
            host_account_id = response.get('PortfolioDetails')[0].get('ARN').split(":")[4]
            sharing_policies = generate_bucket_policies_for_shares(deployment_map, puppet_account_id)
            write_share_template(portfolio_use_by_account, region, host_account_id, sharing_policies)


template_dir = resolve_from_site_packages('templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    extensions=['jinja2.ext.do'],
)

def get_puppet_account_id():
    with betterboto_client.ClientContextManager('sts') as sts:
        return sts.get_caller_identity().get('Account')


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


def get_puppet_version():
    return pkg_resources.require("aws-service-catalog-puppet")[0].version


def expand_path(account, client):
    ou = client.convert_path_to_ou(account.get('ou'))
    account['ou'] = ou
    return expand_ou(account, client)


def expand_ou(original_account, client):
    expanded = []
    response = client.list_children_nested(ParentId=original_account.get('ou'), ChildType='ACCOUNT')
    for result in response:
        new_account_id = result.get('Id')
        response = client.describe_account(AccountId=new_account_id)
        new_account = deepcopy(original_account)
        del new_account['ou']
        if response.get('Account').get('Name') is not None:
            new_account['name'] = response.get('Account').get('Name')
        new_account['email'] = response.get('Account').get('Email')
        new_account['account_id'] = new_account_id
        new_account['expanded_from'] = original_account.get('ou')
        new_account['organization'] = response.get('Account').get('Arn').split(":")[5].split("/")[1]
        expanded.append(new_account)
    return expanded


def _do_bootstrap_org_master(puppet_account_id, cloudformation, puppet_version):
    logger.info('Starting bootstrap of org master')
    stack_name = "{}-org-master".format(BOOTSTRAP_STACK_NAME)
    template = read_from_site_packages('{}.template.yaml'.format(stack_name))
    template = Template(template).render(VERSION=puppet_version)
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
    }
    cloudformation.create_or_update(**args)
    response = cloudformation.describe_stacks(StackName=stack_name)
    if len(response.get('Stacks')) != 1:
        raise Exception("Expected there to be only one {} stack".format(stack_name))
    stack = response.get('Stacks')[0]

    for output in stack.get('Outputs'):
        if output.get('OutputKey') == PUPPET_ORG_ROLE_FOR_EXPANDS_ARN:
            logger.info('Finished bootstrap of org-master')
            return output.get("OutputValue")

    raise Exception("Could not find output: {} in stack: {}".format(PUPPET_ORG_ROLE_FOR_EXPANDS_ARN, stack_name))


def _do_bootstrap_spoke(puppet_account_id, cloudformation, puppet_version):
    logger.info('Starting bootstrap of spoke')
    template = read_from_site_packages('{}-spoke.template.yaml'.format(BOOTSTRAP_STACK_NAME))
    template = Template(template).render(VERSION=puppet_version)
    args = {
        'StackName': "{}-spoke".format(BOOTSTRAP_STACK_NAME),
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
    }
    cloudformation.create_or_update(**args)
    logger.info('Finished bootstrap of spoke')


def _do_bootstrap(puppet_version):
    click.echo('Starting bootstrap')
    ALL_REGIONS = get_regions(os.environ.get("AWS_DEFAULT_REGION"))
    with betterboto_client.MultiRegionClientContextManager('cloudformation', ALL_REGIONS) as clients:
        click.echo('Creating {}-regional'.format(BOOTSTRAP_STACK_NAME))
        threads = []
        template = read_from_site_packages('{}.template.yaml'.format('{}-regional'.format(BOOTSTRAP_STACK_NAME)))
        template = Template(template).render(VERSION=puppet_version)
        args = {
            'StackName': '{}-regional'.format(BOOTSTRAP_STACK_NAME),
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
        }
        for client_region, client in clients.items():
            process = Thread(name=client_region, target=client.create_or_update, kwargs=args)
            process.start()
            threads.append(process)
        for process in threads:
            process.join()
        click.echo('Finished creating {}-regional'.format(BOOTSTRAP_STACK_NAME))

    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        click.echo('Creating {}'.format(BOOTSTRAP_STACK_NAME))
        template = read_from_site_packages('{}.template.yaml'.format(BOOTSTRAP_STACK_NAME))
        template = Template(template).render(VERSION=puppet_version, ALL_REGIONS=ALL_REGIONS)
        args = {
            'StackName': BOOTSTRAP_STACK_NAME,
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
                    'ParameterValue': str(get_org_iam_role_arn()),
                    'UsePreviousValue': False,
                },
            ],
        }
        cloudformation.create_or_update(**args)

    click.echo('Finished creating {}.'.format(BOOTSTRAP_STACK_NAME))
    with betterboto_client.ClientContextManager('codecommit') as codecommit:
        response = codecommit.get_repository(repositoryName=SERVICE_CATALOG_PUPPET_REPO_NAME)
        clone_url = response.get('repositoryMetadata').get('cloneUrlHttp')
        clone_command = "git clone --config 'credential.helper=!aws codecommit credential-helper $@' " \
                        "--config 'credential.UseHttpPath=true' {}".format(clone_url)
        click.echo(
            'You need to clone your newly created repo now and will then need to seed it: \n{}'.format(
                clone_command
            )
        )