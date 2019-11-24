# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import copy
import functools
import sys
import time
from glob import glob
from pathlib import Path

import click
import colorclass
import luigi

import pkg_resources
import json

import terminaltables
from jinja2 import Template
from luigi import LuigiStatusCode

from . import asset_helpers
from . import constants
import logging

import os
from threading import Thread

import yaml

from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@functools.lru_cache(maxsize=32)
def get_config(default_region=None):
    logger.info("getting config,  default_region: {}".format(default_region))
    with betterboto_client.ClientContextManager(
            'ssm',
            region_name=default_region if default_region else get_home_region()
    ) as ssm:
        response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
        return yaml.safe_load(response.get('Parameter').get('Value'))


@functools.lru_cache(maxsize=32)
def get_regions(default_region=None):
    logger.info("getting regions,  default_region: {}".format(default_region))
    return get_config(default_region).get('regions')


@functools.lru_cache(maxsize=32)
def get_should_use_sns(default_region=None):
    logger.info("getting should_use_sns,  default_region: {}".format(default_region))
    return get_config(default_region).get('should_collect_cloudformation_events', True)


@functools.lru_cache(maxsize=32)
def get_should_use_eventbridge(default_region=None):
    logger.info("getting should_use_eventbridge,  default_region: {}".format(default_region))
    return get_config(default_region).get('should_forward_events_to_eventbridge', False)


@functools.lru_cache(maxsize=32)
def get_should_forward_failures_to_opscenter(default_region=None):
    logger.info("getting should_forward_failures_to_opscenter,  default_region: {}".format(default_region))
    return get_config(default_region).get('should_forward_failures_to_opscenter', False)


@functools.lru_cache(maxsize=32)
def get_should_use_product_plans(default_region=None):
    logger.info("getting should_use_product_plans,  default_region: {}".format(default_region))
    return get_config(default_region).get('should_use_product_plans', True)


@functools.lru_cache()
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


template_dir = asset_helpers.resolve_from_site_packages('templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    extensions=['jinja2.ext.do'],
)


@functools.lru_cache(maxsize=32)
def get_puppet_account_id():
    with betterboto_client.ClientContextManager('sts') as sts:
        return sts.get_caller_identity().get('Account')


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
                    new_task = copy.deepcopy(task_2)
                    if new_task.get('depends_on') is not None:
                        del new_task['depends_on']
                    task.get('dependencies').append(new_task)
        del task['depends_on']
        tasks_to_run.append(task)

        for task_to_run in tasks_to_run:
            for dependency in task_to_run.get('dependencies', []):
                dependency['dependencies'] = []

    return tasks_to_run


def get_puppet_version():
    return pkg_resources.require("aws-service-catalog-puppet")[0].version


def _do_bootstrap_org_master(puppet_account_id, cloudformation, puppet_version):
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
        'Tags': [
            {
                "Key": "ServiceCatalogPuppet:Actor",
                "Value": "Framework",
            }
        ]
    }
    cloudformation.create_or_update(**args)
    logger.info('Finished bootstrap of spoke')


def _do_bootstrap(puppet_version, with_manual_approvals):
    click.echo('Starting bootstrap')

    should_use_eventbridge = get_should_use_eventbridge(os.environ.get("AWS_DEFAULT_REGION"))
    if should_use_eventbridge:
        with betterboto_client.ClientContextManager('events') as events:
            try:
                events.describe_event_bus(Name=constants.EVENT_BUS_NAME)
            except events.exceptions.ResourceNotFoundException:
                events.create_event_bus(
                    Name=constants.EVENT_BUS_NAME,
                )

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
                {
                    'ParameterKey': 'WithManualApprovals',
                    'ParameterValue': "Yes" if with_manual_approvals else "No",
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


def run_tasks(tasks_to_run, num_workers, dry_run=False):
    should_use_eventbridge = get_should_use_eventbridge(os.environ.get("AWS_DEFAULT_REGION")) and not dry_run
    should_forward_failures_to_opscenter = get_should_forward_failures_to_opscenter(os.environ.get("AWS_DEFAULT_REGION")) and not dry_run

    ssm_client = None
    if should_forward_failures_to_opscenter:
        with betterboto_client.ClientContextManager('ssm') as ssm:
            ssm_client = ssm

    entries = []

    for type in ["failure", "success", "timeout", "process_failure", "processing_time", "broken_task", ]:
        os.makedirs(Path(constants.RESULTS_DIRECTORY) / type)

    logger.info(f"About to run workflow with {num_workers} workers")

    run_result = luigi.build(
        tasks_to_run,
        local_scheduler=True,
        detailed_summary=True,
        workers=num_workers,
        log_level='INFO',
    )

    exit_status_codes = {
        LuigiStatusCode.SUCCESS: 0,
        LuigiStatusCode.SUCCESS_WITH_RETRY: 0,
        LuigiStatusCode.FAILED: 1,
        LuigiStatusCode.FAILED_AND_SCHEDULING_FAILED: 2,
        LuigiStatusCode.SCHEDULING_FAILED: 3,
        LuigiStatusCode.NOT_RUN: 4,
        LuigiStatusCode.MISSING_EXT: 5,
    }

    click.echo("Results")
    if dry_run:
        table_data = [
            ['Result', 'Launch', 'Account', 'Region', 'Current Version', 'New Version', 'Notes'],

        ]
        table = terminaltables.AsciiTable(table_data)
        for filename in glob('output/TerminateProductDryRunTask/*.json'):
            result = json.loads(open(filename, 'r').read())
            table_data.append([
                result.get('effect'),
                result.get('params').get('launch_name'),
                result.get('params').get('account_id'),
                result.get('params').get('region'),
                result.get('current_version'),
                result.get('new_version'),
                result.get('notes'),
            ])
        for filename in glob('output/ProvisionProductDryRunTask/*.json'):
            result = json.loads(open(filename, 'r').read())
            table_data.append([
                result.get('effect'),
                result.get('params').get('launch_name'),
                result.get('params').get('account_id'),
                result.get('params').get('region'),
                result.get('current_version'),
                result.get('new_version'),
                result.get('notes'),
            ])
        click.echo(table.table)
    else:
        table_data = [
            ['Action', 'Params', 'Duration'],

        ]
        table = terminaltables.AsciiTable(table_data)
        for filename in glob('results/processing_time/*.json'):
            result_contents = open(filename, 'r').read()
            result = json.loads(result_contents)
            params = result.get('params_for_results')
            if should_use_eventbridge:
                entries.append({
                    # 'Time': ,
                    'Source': constants.SERVICE_CATALOG_PUPPET_EVENT_SOURCE,
                    'Resources': [
                        # 'string',
                    ],
                    'DetailType': result.get('task_type'),
                    'Detail': result_contents,
                    'EventBusName': constants.EVENT_BUS_NAME
                })

            params = yaml.safe_dump(params)

            table_data.append([
                result.get('task_type'),
                params,
                result.get('duration'),
            ])
        click.echo(table.table)
        for filename in glob('results/failure/*.json'):
            result = json.loads(open(filename, 'r').read())
            params = result.get('params_for_results')
            if should_forward_failures_to_opscenter:
                title = f"{result.get('task_type')} failed: {params.get('launch_name')} - {params.get('account_id')} - {params.get('region')}"
                logging.info(f"Sending failure to opscenter: {title}")
                operational_data = {}
                for param_name, param in params.items():
                    operational_data[param_name] = {
                        "Value": json.dumps(param, default=str),
                        'Type': 'SearchableString',
                    }
                description = "\n".join(result.get('exception_stack_trace'))[:1024]
                ssm_client.create_ops_item(
                    Title=title,
                    Description=description,
                    OperationalData=operational_data,
                    Priority=1,
                    Source=constants.SERVICE_CATALOG_PUPPET_OPS_CENTER_SOURCE,
                )

            click.echo(colorclass.Color("{red}" + result.get('task_type') + " failed{/red}"))
            click.echo(f"{yaml.safe_dump({'parameters':result.get('task_params')})}")
            click.echo("\n".join(result.get('exception_stack_trace')))
            click.echo('')

        if should_use_eventbridge:
            logging.info(f"Sending {len(entries)} events to eventbridge")
            with betterboto_client.ClientContextManager('events') as events:
                for i in range(0, len(entries), constants.EVENTBRIDGE_MAX_EVENTS_PER_CALL):
                    events.put_events(
                        Entries=entries[i:i+constants.EVENTBRIDGE_MAX_EVENTS_PER_CALL]
                    )
                    time.sleep(1)
            logging.info(f"Finished sending {len(entries)} events to eventbridge")
    sys.exit(exit_status_codes.get(run_result.status))


def run_tasks_for_generate_shares(tasks_to_run):
    for type in ["failure", "success", "timeout", "process_failure", "processing_time", "broken_task", ]:
        os.makedirs(Path(constants.RESULTS_DIRECTORY) / type)

    run_result = luigi.build(
        tasks_to_run,
        local_scheduler=True,
        detailed_summary=True,
        workers=10,
        log_level='INFO',
    )

    should_use_sns = get_should_use_sns()
    puppet_account_id = get_puppet_account_id()
    version = get_puppet_version()

    for region in get_regions():
        sharing_policies = {
            'accounts': [],
            'organizations': [],
        }
        with betterboto_client.ClientContextManager('cloudformation', region_name=region) as cloudformation:
            cloudformation.ensure_deleted(StackName="servicecatalog-puppet-shares")

            logger.info(f"generating policies collection for region {region}")
            if os.path.exists(os.path.sep.join(['data', 'bucket'])):
                logger.info(f"Updating policies for the region: {region}")
                path = os.path.sep.join(['data', 'bucket', region, 'accounts'])
                if os.path.exists(path):
                    for account_file in os.listdir(path):
                        account = account_file.split(".")[0]
                        sharing_policies['accounts'].append(account)

                path = os.path.sep.join(['data', 'bucket', region, 'organizations'])
                if os.path.exists(path):
                    for organization_file in os.listdir(path):
                        organization = organization_file.split(".")[0]
                        sharing_policies['organizations'].append(organization)

            logger.info(f"Finished generating policies collection")

            template = env.get_template('policies.template.yaml.j2').render(
                sharing_policies=sharing_policies,
                VERSION=version,
            )
            with betterboto_client.ClientContextManager('cloudformation', region_name=region) as cloudformation:
                cloudformation.create_or_update(
                    StackName="servicecatalog-puppet-policies",
                    TemplateBody=template,
                    NotificationARNs=[
                        f"arn:aws:sns:{region}:{puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                    ] if should_use_sns else [],
                )

    for filename in glob('results/failure/*.json'):
        result = json.loads(open(filename, 'r').read())
        click.echo(colorclass.Color("{red}" + result.get('task_type') + " failed{/red}"))
        click.echo(f"{yaml.safe_dump({'parameters':result.get('task_params')})}")
        click.echo("\n".join(result.get('exception_stack_trace')))
        click.echo('')
    exit_status_codes = {
        LuigiStatusCode.SUCCESS: 0,
        LuigiStatusCode.SUCCESS_WITH_RETRY: 0,
        LuigiStatusCode.FAILED: 1,
        LuigiStatusCode.FAILED_AND_SCHEDULING_FAILED: 2,
        LuigiStatusCode.SCHEDULING_FAILED: 3,
        LuigiStatusCode.NOT_RUN: 4,
        LuigiStatusCode.MISSING_EXT: 5,
    }
    sys.exit(exit_status_codes.get(run_result.status))


def run_tasks_for_bootstrap_spokes_in_ou(tasks_to_run):
    for type in ["failure", "success", "timeout", "process_failure", "processing_time", "broken_task", ]:
        os.makedirs(Path(constants.RESULTS_DIRECTORY) / type)

    run_result = luigi.build(
        tasks_to_run,
        local_scheduler=True,
        detailed_summary=True,
        workers=10,
        log_level='INFO',
    )

    for filename in glob('results/failure/*.json'):
        result = json.loads(open(filename, 'r').read())
        click.echo(colorclass.Color("{red}" + result.get('task_type') + " failed{/red}"))
        click.echo(f"{yaml.safe_dump({'parameters':result.get('task_params')})}")
        click.echo("\n".join(result.get('exception_stack_trace')))
        click.echo('')
    exit_status_codes = {
        LuigiStatusCode.SUCCESS: 0,
        LuigiStatusCode.SUCCESS_WITH_RETRY: 0,
        LuigiStatusCode.FAILED: 1,
        LuigiStatusCode.FAILED_AND_SCHEDULING_FAILED: 2,
        LuigiStatusCode.SCHEDULING_FAILED: 3,
        LuigiStatusCode.NOT_RUN: 4,
        LuigiStatusCode.MISSING_EXT: 5,
    }
    sys.exit(exit_status_codes.get(run_result.status))
