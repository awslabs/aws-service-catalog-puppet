# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import cfn_tools
import requests
from colorclass import Color
import terminaltables

import shutil
import json

import pkg_resources
import yaml
import logging
import os
import click

from jinja2 import Template
from pykwalify.core import Core
from betterboto import client as betterboto_client

from servicecatalog_puppet import cli_command_helpers
from servicecatalog_puppet import luigi_tasks_and_targets
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
    puppet_account_id = cli_command_helpers.get_puppet_account_id()
    manifest = manifest_utils.load(f)

    deployment_map = manifest_utils.build_deployment_map(manifest, constants.LAUNCHES)
    for account_id, deployment_map_for_account in deployment_map.items():
        tasks_to_run.append(
            luigi_tasks_and_targets.CreateSharesForAccountImportMapTask(
                account_id=account_id,
                puppet_account_id=puppet_account_id,
                deployment_map_for_account=deployment_map_for_account,
                sharing_type='launches',
            )
        )

    import_map = manifest_utils.build_deployment_map(manifest, constants.SPOKE_LOCAL_PORTFOLIOS)
    for account_id, import_map_for_account in import_map.items():
        tasks_to_run.append(
            luigi_tasks_and_targets.CreateSharesForAccountImportMapTask(
                account_id=account_id,
                puppet_account_id=puppet_account_id,
                deployment_map_for_account=import_map_for_account,
                sharing_type='spoke-local-portfolios',
            )
        )

    cli_command_helpers.run_tasks_for_generate_shares(tasks_to_run)


def dry_run(f):
    puppet_account_id = cli_command_helpers.get_puppet_account_id()
    manifest = manifest_utils.load(f)

    launch_tasks = {}
    tasks_to_run = []

    all_launch_tasks = cli_command_helpers.deploy_launches(manifest, puppet_account_id)
    launch_tasks.update(all_launch_tasks)

    for task in cli_command_helpers.wire_dependencies(launch_tasks):
        task_status = task.get('status')
        del task['status']
        if task_status == constants.PROVISIONED:
            tasks_to_run.append(luigi_tasks_and_targets.ProvisionProductDryRunTask(**task))
        elif task_status == constants.TERMINATED:
            tasks_to_run.append(luigi_tasks_and_targets.TerminateProductDryRunTask(**task))
        else:
            raise Exception(f"Unsupported status of {task_status}")

    # spoke_local_portfolio_tasks_to_run = cli_command_helpers.deploy_spoke_local_portfolios(manifest, launch_tasks)
    # tasks_to_run += spoke_local_portfolio_tasks_to_run

    cli_command_helpers.run_tasks_for_dry_run(tasks_to_run)


def reset_provisioned_product_owner(f):
    puppet_account_id = cli_command_helpers.get_puppet_account_id()
    manifest = manifest_utils.load(f)

    launch_tasks = {}
    tasks_to_run = []

    all_launch_tasks = cli_command_helpers.deploy_launches(manifest, puppet_account_id)
    launch_tasks.update(all_launch_tasks)

    for task in cli_command_helpers.wire_dependencies(launch_tasks):
        task_status = task.get('status')
        del task['status']
        if task_status == constants.PROVISIONED:
            tasks_to_run.append(luigi_tasks_and_targets.ResetProvisionedProductOwnerTask(**task))

    cli_command_helpers.run_tasks(tasks_to_run)


def deploy(f, single_account):
    puppet_account_id = cli_command_helpers.get_puppet_account_id()

    manifest = manifest_utils.load(f)

    launch_tasks = {}
    tasks_to_run = []

    should_use_sns = cli_command_helpers.get_should_use_sns(os.environ.get("AWS_DEFAULT_REGION"))

    all_launch_tasks = cli_command_helpers.deploy_launches(manifest, puppet_account_id)
    launch_tasks.update(all_launch_tasks)


    for task in cli_command_helpers.wire_dependencies(launch_tasks):
        task_status = task.get('status')
        del task['status']
        if task_status == constants.PROVISIONED:
            task['should_use_sns'] = should_use_sns
            tasks_to_run.append(luigi_tasks_and_targets.ProvisionProductTask(**task))
        elif task_status == constants.TERMINATED:
            for attribute in constants.DISALLOWED_ATTRIBUTES_FOR_TERMINATED_LAUNCHES:
                logger.info(f"checking {task.get('launch_name')} for disallowed attributes")
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

            tasks_to_run.append(luigi_tasks_and_targets.TerminateProductTask(**task))
        else:
            raise Exception(f"Unsupported status of {task_status}")

    spoke_local_portfolio_tasks_to_run = cli_command_helpers.deploy_spoke_local_portfolios(
        manifest, launch_tasks, should_use_sns, puppet_account_id
    )
    tasks_to_run += spoke_local_portfolio_tasks_to_run

    cli_command_helpers.run_tasks(tasks_to_run)


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
        cli_command_helpers._do_bootstrap_spoke(puppet_account_id, cloudformation,
                                                cli_command_helpers.get_puppet_version())


def bootstrap_spoke(puppet_account_id):
    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        cli_command_helpers._do_bootstrap_spoke(puppet_account_id, cloudformation,
                                                cli_command_helpers.get_puppet_version())


def bootstrap_branch(branch_name, with_manual_approvals):
    cli_command_helpers._do_bootstrap(
        "https://github.com/awslabs/aws-service-catalog-puppet/archive/{}.zip".format(branch_name),
        with_manual_approvals,
    )


def bootstrap(with_manual_approvals):
    cli_command_helpers._do_bootstrap(
        cli_command_helpers.get_puppet_version(),
        with_manual_approvals,
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
    ALL_REGIONS = cli_command_helpers.get_regions(os.environ.get("AWS_DEFAULT_REGION"))
    deployment_map = manifest_utils.build_deployment_map(manifest, constants.LAUNCHES)
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
    for account_id, details in deployment_map.items():
        for launch_name, launch in details.get(constants.LAUNCHES, {}).items():
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
                        'expected_version': launch.get('version'),
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
                Color("{green}" + result.get('actual_version') + "{/green}") if result.get('actual_version') == result.get('expected_version') else Color("{red}" + result.get('actual_version') + "{/red}"),
                Color("{green}" + str(result.get('active')) + "{/green}") if result.get('active') else Color("{red}" + str(result.get('active')) + "{/red}"),
                Color("{green}" + result.get('status') + "{/green}") if result.get('status') == "AVAILABLE" else Color("{red}" + result.get('status') + "{/red}")
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
