# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import click

import pkg_resources
import json
from jinja2 import Template

from servicecatalog_puppet import asset_helpers, manifest_utils, aws, luigi_tasks_and_targets
from servicecatalog_puppet import constants
import logging

import os
from threading import Thread

import yaml
from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_regions(default_region=None):
    logger.info("getting regions,  default_region: {}".format(default_region))
    with betterboto_client.ClientContextManager(
            'ssm',
            region_name=default_region if default_region else get_home_region()
    ) as ssm:
        response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
        config = yaml.safe_load(response.get('Parameter').get('Value'))
        return config.get('regions')


def get_home_region():
    with betterboto_client.ClientContextManager('ssm') as ssm:
        response = ssm.get_parameter(Name=constants.HOME_REGION_PARAM_NAME)
        return response.get('Parameter').get('Value')


def get_org_iam_role_arn():
    with betterboto_client.ClientContextManager('ssm', region_name=get_home_region()) as ssm:
        try:
            response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN)
            return yaml.safe_load(response.get('Parameter').get('Value'))
        except ssm.exceptions.ParameterNotFound as e:
            logger.info("No parameter set for: {}".format(constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN))
            return None


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
    output = os.path.sep.join([constants.TEMPLATES, 'shares', region])
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


def create_share_template(deployment_map, import_map, puppet_account_id):
    logger.info("deployment_map: {}".format(deployment_map))
    ALL_REGIONS = get_regions()
    for region in ALL_REGIONS:
        logger.info("starting to build shares for region: {}".format(region))
        with betterboto_client.ClientContextManager('servicecatalog', region_name=region) as servicecatalog:
            portfolio_ids = {}

            response = servicecatalog.list_portfolios_single_page()

            for portfolio_detail in response.get('PortfolioDetails'):
                portfolio_ids[portfolio_detail.get('DisplayName')] = portfolio_detail.get('Id')

            logger.info("Portfolios in use in region: {}".format(portfolio_ids))

            portfolio_use_by_account = {}
            for account_id, launch_details in deployment_map.items():
                if portfolio_use_by_account.get(account_id) is None:
                    portfolio_use_by_account[account_id] = []
                for launch_id, launch in launch_details.get('launches').items():
                    p = portfolio_ids[launch.get('portfolio')]
                    if p not in portfolio_use_by_account[account_id]:
                        portfolio_use_by_account[account_id].append(p)

            for account_id, import_details in import_map.items():
                if portfolio_use_by_account.get(account_id) is None:
                    portfolio_use_by_account[account_id] = []
                for spoke_local_portfolio_id, spoke_local_portfolio in import_details.get('spoke-local-portfolios').items():
                    p = portfolio_ids[spoke_local_portfolio.get('portfolio')]
                    if p not in portfolio_use_by_account[account_id]:
                        portfolio_use_by_account[account_id].append(p)

            host_account_id = response.get('PortfolioDetails')[0].get('ARN').split(":")[4]
            sharing_policies = generate_bucket_policies_for_shares(deployment_map, puppet_account_id)
            write_share_template(portfolio_use_by_account, region, host_account_id, sharing_policies)


template_dir = asset_helpers.resolve_from_site_packages('templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    extensions=['jinja2.ext.do'],
)


def get_puppet_account_id():
    with betterboto_client.ClientContextManager('sts') as sts:
        return sts.get_caller_identity().get('Account')


def set_regions_for_deployment_map(deployment_map, section):
    logger.info('Starting to write the templates')
    ALL_REGIONS = get_regions()
    for account_id, account_details in deployment_map.items():
        for launch_name, launch_details in account_details.get(section).items():
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

            if section == constants.LAUNCHES:
                # TODO move this to provision product task so this if statement is no longer needed
                for region in launch_details.get('regions'):
                    logger.info('Starting region: {}'.format(region))
                    product_id, version_id = aws.get_provisioning_artifact_id_for(
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
        account_ssm_param = deployment_map.get(account_id).get('parameters', {}).get(required_parameter_name, {}).get(
            'ssm')
        account_regular_param = deployment_map.get(account_id).get('parameters', {}).get(required_parameter_name,
                                                                                         {}).get('default')

        launch_params = launch_details.get('parameters', {})
        launch_ssm_param = launch_params.get(required_parameter_name, {}).get('ssm')
        launch_regular_param = launch_params.get(required_parameter_name, {}).get('default')

        manifest_params = manifest.get('parameters', {})
        manifest_ssm_param = manifest_params.get(required_parameter_name, {}).get('ssm')
        manifest_regular_param = manifest_params.get(required_parameter_name, {}).get('default')

        if status == constants.PROVISIONED and account_ssm_param:
            ssm_parameters.append(
                get_ssm_config_for_parameter(account_ssm_param, required_parameter_name)
            )
        elif status == constants.PROVISIONED and account_regular_param:
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

        elif status == constants.PROVISIONED and manifest_ssm_param:
            ssm_parameters.append(
                get_ssm_config_for_parameter(manifest_ssm_param, required_parameter_name)
            )
        elif status == constants.PROVISIONED and manifest_regular_param:
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
        tasks_to_run.append(task)
    return tasks_to_run


def get_puppet_version():
    return pkg_resources.require("aws-service-catalog-puppet")[0].version


def _do_bootstrap_org_master(puppet_account_id, cloudformation, puppet_version):
    logger.info('Starting bootstrap of org master')
    stack_name = "{}-org-master".format(constants.BOOTSTRAP_STACK_NAME)
    template = asset_helpers.read_from_site_packages('{}.template.yaml'.format(stack_name))
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
        if output.get('OutputKey') == constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN:
            logger.info('Finished bootstrap of org-master')
            return output.get("OutputValue")

    raise Exception(
        "Could not find output: {} in stack: {}".format(constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN, stack_name))


def _do_bootstrap_spoke(puppet_account_id, cloudformation, puppet_version):
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
        template = Template(template).render(VERSION=puppet_version, ALL_REGIONS=ALL_REGIONS)
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
                    'ParameterValue': str(get_org_iam_role_arn()),
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


def deploy_spoke_local_portfolios(manifest, launch_tasks):
    section = constants.SPOKE_LOCAL_PORTFOLIOS
    deployment_map = manifest_utils.build_deployment_map(manifest, section)
    deployment_map = set_regions_for_deployment_map(deployment_map, section)

    tasks_to_run = []
    puppet_account_id = get_puppet_account_id()

    for account_id, deployments_for_account in deployment_map.items():
        for launch_name, launch_details in deployments_for_account.get(section).items():
            for region_name in launch_details.get('regions'):

                depends_on = launch_details.get('depends_on')
                dependencies = []
                for dependency in depends_on:
                    for task_uid, task in launch_tasks.items():
                        if task.get('launch_name') == dependency:
                            dependencies.append(task)

                hub_portfolio = aws.get_portfolio_for(
                    launch_details.get('portfolio'), puppet_account_id, region_name
                )

                create_spoke_local_portfolio_task_params = {
                    'account_id': account_id,
                    'region': region_name,
                    'portfolio': launch_details.get('portfolio'),
                    'provider_name': hub_portfolio.get('ProviderName'),
                    'description': hub_portfolio.get('Description'),
                }
                create_spoke_local_portfolio_task = luigi_tasks_and_targets.CreateSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_params
                )
                tasks_to_run.append(create_spoke_local_portfolio_task)

                create_spoke_local_portfolio_task_as_dependency_params = {
                    'account_id': account_id,
                    'region': region_name,
                    'portfolio': launch_details.get('portfolio'),
                }

                create_associations_task_params = {
                    'associations': launch_details.get('associations'),
                    'puppet_account_id': puppet_account_id,
                }
                create_associations_for_portfolio_task = luigi_tasks_and_targets.CreateAssociationsForPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    **create_associations_task_params,
                    dependencies=dependencies,
                )
                tasks_to_run.append(create_associations_for_portfolio_task)

                import_into_spoke_local_portfolio_task_params = {
                    'hub_portfolio_id': hub_portfolio.get('Id')
                }
                import_into_spoke_local_portfolio_task = luigi_tasks_and_targets.ImportIntoSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    **import_into_spoke_local_portfolio_task_params,
                )
                tasks_to_run.append(import_into_spoke_local_portfolio_task)

                create_launch_role_constraints_for_portfolio_task_params = {
                    'launch_constraints': launch_details.get('constraints', {}).get('launch', []),
                    'puppet_account_id': puppet_account_id,
                }
                create_launch_role_constraints_for_portfolio = luigi_tasks_and_targets.CreateLaunchRoleConstraintsForPortfolio(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    **import_into_spoke_local_portfolio_task_params,
                    **create_launch_role_constraints_for_portfolio_task_params,
                    dependencies=dependencies,
                )
                tasks_to_run.append(create_launch_role_constraints_for_portfolio)

    return tasks_to_run


def deploy_launches(manifest):
    section = constants.LAUNCHES
    deployment_map = manifest_utils.build_deployment_map(manifest, section)
    deployment_map = set_regions_for_deployment_map(deployment_map, section)
    puppet_account_id = get_puppet_account_id()

    all_tasks = deploy_launches_task_builder(deployment_map, manifest, puppet_account_id, section)

    logger.info(f"Deployment plan: {json.dumps(all_tasks)}")
    return all_tasks


def deploy_launches_task_builder(deployment_map, manifest, puppet_account_id, section):
    all_tasks = {}
    for account_id, deployments_for_account in deployment_map.items():
        for launch_name, launch_details in deployments_for_account.get(section).items():
            for region_name, regional_details in launch_details.get('regional_details').items():
                these_all_tasks = deploy_launches_task_builder_for_account_launch_region(
                    account_id,
                    deployment_map,
                    launch_details,
                    launch_name,
                    manifest,
                    puppet_account_id,
                    region_name,
                    regional_details,
                )
                all_tasks.update(these_all_tasks)

    return all_tasks


def deploy_launches_task_builder_for_account_launch_region(
        account_id, deployment_map, launch_details, launch_name, manifest,
        puppet_account_id, region_name, regional_details
):
    all_tasks = {}
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

        "worker_timeout": launch_details.get('timeoutInSeconds', constants.DEFAULT_TIMEOUT),

        "ssm_param_outputs": launch_details.get('outputs', {}).get('ssm', []),

        'dependencies': [],
    }
    if manifest.get('configuration'):
        if manifest.get('configuration').get('retry_count'):
            task['retry_count'] = manifest.get('configuration').get('retry_count')
    if launch_details.get('configuration'):
        if launch_details.get('configuration').get('retry_count'):
            task['retry_count'] = launch_details.get('configuration').get('retry_count')

    all_tasks[f"{task.get('account_id')}-{task.get('region')}-{task.get('launch_name')}"] = task
    return all_tasks
