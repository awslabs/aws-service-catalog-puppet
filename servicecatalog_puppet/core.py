import logging
import os
import time
from copy import deepcopy
from threading import Thread

import click
import pkg_resources
import yaml
from betterboto import client as betterboto_client
from jinja2 import Template, Environment, FileSystemLoader

from asset_helpers import read_from_site_packages, resolve_from_site_packages
from constants import HOME_REGION, CONFIG_PARAM_NAME, CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN, TEMPLATES, PREFIX, \
    BOOTSTRAP_STACK_NAME, SERVICE_CATALOG_PUPPET_REPO_NAME
from macros import macros


logger = logging.getLogger()


def get_regions():
    with betterboto_client.ClientContextManager('ssm', region_name=HOME_REGION) as ssm:
        response = ssm.get_parameter(Name=CONFIG_PARAM_NAME)
        config = yaml.safe_load(response.get('Parameter').get('Value'))
        return config.get('regions')


def get_org_iam_role_arn():
    with betterboto_client.ClientContextManager('ssm', region_name=HOME_REGION) as ssm:
        try:
            response = ssm.get_parameter(Name=CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN)
            return yaml.safe_load(response.get('Parameter').get('Value'))
        except ssm.exceptions.ParameterNotFound as e:
            logger.info("No parameter set for: {}".format(CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN))
            return None


def check_for_duplicate_products_in_launches(launches_by_product):
    logger.info('Checking for duplicate products by tag')
    for product_name, product_launches in launches_by_product.items():
        tags_seen = {}
        for product_launch in product_launches:
            for tag in product_launch.get('deploy_to').get('tags', []):
                tag_name = tag.get('tag')
                if tags_seen.get(tag_name) is None:
                    tags_seen[tag_name] = product_launch
                else:
                    raise Exception(
                        "Cannot process {}.  Already added {} because of tag: {}".format(
                            product_launch.get('launch_name'),
                            tags_seen[tag_name].get('launch_name'),
                            tag_name
                        )
                    )
    logger.info('Finished checking for duplicate products by tag')

    logger.info('Checking for duplicate products by account listed twice')
    for product_name, product_launches in launches_by_product.items():
        accounts_seen = {}
        for product_launch in product_launches:
            for account in product_launch.get('deploy_to').get('accounts', []):
                account_id = account.get('account_id')
                if accounts_seen.get(account_id) is None:
                    accounts_seen[account_id] = product_launch
                else:
                    raise Exception(
                        "Cannot process {}. {} is already receiving product: {} as it was listed in launch: {}".format(
                            product_launch.get('launch_name'),
                            account_id,
                            accounts_seen[account_id].get('product'),
                            accounts_seen[account_id].get('launch_name'),
                        )
                    )
    logger.info('Finished checking for duplicate products by account listed twice')


def group_by_tag(launches):
    logger.info('Grouping launches by tag')
    launches_by_tag = {}
    for launch_name, launch_details in launches.items():
        launch_details['launch_name'] = launch_name
        launch_tags = launch_details.get('deploy_to').get('tags', [])
        for tag_detail in launch_tags:
            tag = tag_detail.get('tag')
            if launches_by_tag.get(tag) is None:
                launches_by_tag[tag] = []
            launches_by_tag[tag].append(launch_details)
    logger.info('Finished grouping launches by tag')
    return launches_by_tag


def group_by_account(launches):
    logger.info('Grouping launches by account')
    launches_by_account = {}
    for launch_name, launch_details in launches.items():
        launch_details['launch_name'] = launch_name
        launch_accounts = launch_details.get('deploy_to').get('accounts', [])
        for account_detail in launch_accounts:
            account_id = account_detail.get('account_id')
            if launches_by_account.get(account_id) is None:
                launches_by_account[account_id] = []
            launches_by_account[account_id].append(launch_details)
    logger.info('Finished grouping launches by account')
    return launches_by_account


def group_by_product(launches):
    logger.info('Grouping launches by product')
    launches_by_product = {}
    for launch_name, launch_details in launches.items():
        product = launch_details.get('product')
        if launches_by_product.get(product) is None:
            launches_by_product[product] = []
        launch_details['launch_name'] = launch_name
        launches_by_product[product].append(launch_details)
    logger.info('Finished grouping launches by product')
    return launches_by_product


def generate_launch_map(accounts, launches_by_account, launches_by_tag):
    logger.info('Generating launch map')
    deployment_map = {}
    for account in accounts:
        account_id = account.get('account_id')
        deployment_map[account_id] = account
        launches = account['launches'] = {}
        for launch in launches_by_account.get(account_id, []):
            launch['match'] = "account_match"
            launches[launch.get('launch_name')] = launch
        for tag in account.get('tags'):
            for launch in launches_by_tag.get(tag, []):
                launch['match'] = "tag_match"
                launch['matching_tag'] = tag
                launches[launch.get('launch_name')] = launch
    logger.info('Finished generating launch map')
    return deployment_map


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


def write_templates(deployment_map):
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
                        elif regions == "default_region":
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
                        elif regions == "default_region":
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
            for region in launch_details.get('regions'):
                logger.info('Starting region: {}'.format(region))
                launch_details['product_id'], launch_details[
                    'provisioning_artifact_id'] = get_provisioning_artifact_id_for(
                    launch_details.get('portfolio'),
                    launch_details.get('product'),
                    launch_details.get('version'),
                    account_id,
                    region
                )
                path = os.sep.join([TEMPLATES, account_id, region])
                if not os.path.exists(path):
                    os.makedirs(path)
                with open(os.sep.join([path, "{}.template.yaml".format(launch_details.get('launch_name'))]), 'w') as f:
                    f.write(
                        env.get_template('product.template.yaml.j2').render(
                            launch_name=launch_name, launch_details=launch_details
                        )
                    )
    logger.info('Finished writing the templates')


def generate_bucket_policies_for_shares(deployment_map):
    shares = {
        'accounts': [],
        'organizations': [],
    }
    for account_id, deployment in deployment_map.items():
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
                HOME_REGION=HOME_REGION,
                sharing_policies=sharing_policies,
            )
        )


def verify_no_ous_in_manifest(accounts):
    for account in accounts:
        if account.get('account_id') is None:
            raise Exception("{} account object does not have an account_id".format(account.get('name')))


def build_deployment_map(manifest):
    accounts = manifest.get('accounts')
    launches = manifest.get('launches')

    verify_no_ous_in_manifest(accounts)

    launches_by_product = group_by_product(launches)
    # check_for_duplicate_products_in_launches(launches_by_product)
    launches_by_tag = group_by_tag(launches)
    launches_by_account = group_by_account(launches)

    return generate_launch_map(
        accounts,
        launches_by_account,
        launches_by_tag,
    )


def create_share_template(deployment_map):
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
                    logger.info(portfolio_ids)
                    p = portfolio_ids[launch.get('portfolio')]
                    if p not in portfolio_use_by_account[account_id]:
                        portfolio_use_by_account[account_id].append(p)
            host_account_id = response.get('PortfolioDetails')[0].get('ARN').split(":")[4]
            sharing_policies = generate_bucket_policies_for_shares(deployment_map)
            write_share_template(portfolio_use_by_account, region, host_account_id, sharing_policies)


def deploy_launches(deployment_map, parameters, single_account, puppet_account_id):
    logger.info('Deploying launches')
    streams = {}
    threads = []
    for account_id, deployments in deployment_map.items():
        if single_account is None or account_id == single_account:
            for launch_name, launch_details in deployments.get('launches').items():
                for region in launch_details.get('regions', []):
                    stream_name = "{}/{}".format(account_id, region)
                    if streams.get(stream_name) is None:
                        streams[stream_name] = []
                    location = 0
                    for dependency in launch_details.get('depends_on', []):
                        for l in streams[stream_name]:
                            if l.get('launch_name') == dependency:
                                location = streams[stream_name].index(l) + 1
                                print(location)
                    streams[stream_name].insert(location, launch_details)

    for stream_name, stream in streams.items():
        process = Thread(
            name=stream_name,
            target=process_stream,
            args=[stream_name, stream, parameters, puppet_account_id, deployment_map]
        )
        process.start()
        threads.append(process)
    for thread in threads:
        thread.join()


def is_launch_deployed_to_account_and_region_already(service_catalog, launch, provisioning_artifact_id, product_id):
    logger.info('is launch: {} deployed'.format(launch.get('launch_name')))

    response = service_catalog.search_provisioned_products(
        Filters={'SearchQuery': [
            "productId:{}".format(product_id)
        ]}
    )

    for r in response.get('ProvisionedProducts', []):
        if r.get('Name') == launch.get('launch_name'):
            if r.get('Status') == "AVAILABLE" and False:
                logger.info("Product and version has been provisioned already")
                if r.get('ProvisioningArtifactId') == provisioning_artifact_id:
                    return True
                else:
                    return False
            else:
                logger.info("Product and version needs terminating: {}".format(r.get('Status')))
                service_catalog.terminate_provisioned_product(
                    ProvisionedProductId=r.get('Id')
                )
                logger.info("now waiting for delete")
                while True:
                    response = service_catalog.search_provisioned_products(
                        Filters={
                            'SearchQuery': ['name:{}'.format(launch.get('launch_name'))]
                        }
                    )
                    if len(response.get('ProvisionedProducts')) > 0:
                        time.sleep(5)
                    else:
                        break
    return False


def deploy_launch_to_account_and_region(
        service_catalog,
        launch,
        account,
        region,
        product_id,
        provisioning_artifact_id,
        provisioned_product_name,
        puppet_account_id,
        path_id,
        params
):
    launch_name = launch.get('launch_name')
    stack_name = "-".join([PREFIX, account, region, launch_name])

    logger.info('Creating plan, params: {}'.format(params))
    response = service_catalog.create_provisioned_product_plan(
        PlanName=stack_name,
        PlanType='CLOUDFORMATION',
        PathId=path_id,
        ProductId=product_id,
        ProvisionedProductName=provisioned_product_name,
        ProvisioningArtifactId=provisioning_artifact_id,
        ProvisioningParameters=params,
        Tags=[
            {
                'Key': 'launch_name',
                'Value': launch_name,
            }
        ],
        NotificationArns=[
            "arn:aws:sns:{}:{}:servicecatalog-puppet-cloudformation-events".format(
                HOME_REGION,
                puppet_account_id
            ),
        ],
    )
    logger.info('Plan created, waiting for completion')

    plan_id = response.get('PlanId')
    plan_status = 'CREATE_IN_PROGRESS'

    while plan_status == 'CREATE_IN_PROGRESS':
        response = service_catalog.describe_provisioned_product_plan(
            PlanId=plan_id
        )
        plan_status = response.get('ProvisionedProductPlanDetails').get('Status')
        logger.info('Waiting for product plan: {}'.format(plan_status))
        time.sleep(5)

    if plan_status == 'CREATE_SUCCESS':
        logger.info(
            'Changes in the product: {}'.format(
                yaml.safe_dump(response.get('ResourceChanges'))
            )
        )
    else:
        raise Exception(
            "Plan was not successful: {}".format(
                response.get('ProvisionedProductPlanDetails').get('StatusMessage')
            )
        )

    logger.info("Executing product plan")
    service_catalog.execute_provisioned_product_plan(PlanId=plan_id)
    execute_status = 'EXECUTE_IN_PROGRESS'
    while execute_status == 'EXECUTE_IN_PROGRESS':
        response = service_catalog.describe_provisioned_product_plan(
            PlanId=plan_id
        )
        execute_status = response.get('ProvisionedProductPlanDetails').get('Status')
        logger.info('Waiting for execute: {}'.format(execute_status))
        time.sleep(5)

    if execute_status == 'CREATE_SUCCESS':
        logger.info("Product provisioned")
    else:
        raise Exception("Execute was not successful: {}".format(execute_status))
    service_catalog.delete_provisioned_product_plan(PlanId=plan_id)


def generate_params(account, deployment_map, launch_name, parameters, path_id, product_id, provisioning_artifact_id,
                    service_catalog):
    response = service_catalog.describe_provisioning_parameters(
        ProductId=product_id,
        ProvisioningArtifactId=provisioning_artifact_id,
        PathId=path_id,
    )
    params = []
    for provisioning_artifact_parameters in response.get('ProvisioningArtifactParameters', []):
        parameter_key = provisioning_artifact_parameters.get('ParameterKey')
        if deployment_map.get(account).get('parameters', {}).get(parameter_key, {}).get('default'):
            params.append({
                'Key': str(parameter_key),
                'Value': str(deployment_map.get(account).get('parameters', {}).get(parameter_key, {}).get(
                    'default'))
            })
        elif deployment_map.get(account).get('launches', {}).get(launch_name, {}).get('parameters', {}).get(
                parameter_key, {}).get('default'):
            params.append({
                'Key': str(parameter_key),
                'Value': str(deployment_map.get(account).get('launches', {}).get(launch_name, {}).get(
                    'parameters', {}).get(parameter_key, {}).get('default'))
            })
        elif parameters.get(parameter_key, {}).get('default'):
            params.append({
                'Key': str(parameter_key),
                'Value': str(parameters.get(parameter_key, {}).get('default'))
            })
    return params


def process_stream(stream_name, stream, parameters, puppet_account_id, deployment_map):
    logger.info("Processing stream of length: {}".format(len(stream)))

    account, region = stream_name.split("/")
    role = "arn:aws:iam::{}:role/{}".format(account, 'servicecatalog-puppet/PuppetRole')
    with betterboto_client.CrossAccountClientContextManager(
            'servicecatalog', role, stream_name.replace("/", "-")
    ) as service_catalog:
        for launch in stream:
            logger.info('is launch: {} deployed'.format(launch.get('launch_name')))
            path = os.path.sep.join([
                TEMPLATES,
                account,
                region,
                "{}.template.yaml".format(launch.get('launch_name'))
            ])
            template_contents = open(path, 'r').read()
            template = yaml.safe_load(template_contents)
            template_properties = template.get('Resources').get('CloudFormationProvisionedProduct').get(
                'Properties')
            product_id = template_properties.get('ProductId')
            provisioning_artifact_id = template_properties.get('ProvisioningArtifactId')
            provisioned_product_name = template_properties.get('ProvisionedProductName')
            launch_name = launch.get('launch_name')

            if not is_launch_deployed_to_account_and_region_already(
                    service_catalog,
                    launch,
                    provisioning_artifact_id,
                    product_id,
            ):
                logger.info('Getting path for product')
                response = service_catalog.list_launch_paths(ProductId=product_id)
                if len(response.get('LaunchPathSummaries')) != 1:
                    raise Exception("Found unexpected amount of LaunchPathSummaries")
                path_id = response.get('LaunchPathSummaries')[0].get('Id')
                logger.info('Got path for product')

                params = generate_params(
                    account,
                    deployment_map,
                    launch_name,
                    parameters,
                    path_id,
                    product_id,
                    provisioning_artifact_id,
                    service_catalog
                )

                deploy_launch_to_account_and_region(
                    service_catalog,
                    launch,
                    account,
                    region,
                    product_id,
                    provisioning_artifact_id,
                    provisioned_product_name,
                    puppet_account_id,
                    path_id,
                    params,
                )

    logger.info('Finished creating stacks')


def do_bootstrap_spoke(puppet_account_id, cloudformation):
    logger.info('Starting bootstrap of spoke')
    template = read_from_site_packages('{}-spoke.template.yaml'.format(BOOTSTRAP_STACK_NAME))
    template = Template(template).render(VERSION=VERSION)
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
                'ParameterValue': VERSION,
                'UsePreviousValue': False,
            },
        ],
    }
    cloudformation.create_or_update(**args)
    logger.info('Finished bootstrap of spoke')


def do_bootstrap():
    click.echo('Starting bootstrap')
    ALL_REGIONS = get_regions()
    with betterboto_client.MultiRegionClientContextManager('cloudformation', ALL_REGIONS) as clients:
        click.echo('Creating {}-regional'.format(BOOTSTRAP_STACK_NAME))
        threads = []
        template = read_from_site_packages('{}.template.yaml'.format('{}-regional'.format(BOOTSTRAP_STACK_NAME)))
        template = Template(template).render(VERSION=VERSION)
        args = {
            'StackName': '{}-regional'.format(BOOTSTRAP_STACK_NAME),
            'TemplateBody': template,
            'Capabilities': ['CAPABILITY_IAM'],
            'Parameters': [
                {
                    'ParameterKey': 'Version',
                    'ParameterValue': VERSION,
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
        template = Template(template).render(VERSION=VERSION, ALL_REGIONS=ALL_REGIONS)
        args = {
            'StackName': BOOTSTRAP_STACK_NAME,
            'TemplateBody': template,
            'Capabilities': ['CAPABILITY_NAMED_IAM'],
            'Parameters': [
                {
                    'ParameterKey': 'Version',
                    'ParameterValue': VERSION,
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


def do_expand(manifest, client):
    new_manifest = deepcopy(manifest)
    new_accounts = new_manifest['accounts'] = []

    logger.info('Starting the expand')

    for account in manifest.get('accounts'):
        if account.get('account_id'):
            logger.info("Found an account: {}".format(account.get('account_id')))
            new_accounts.append(account)
        elif account.get('ou'):
            ou = account.get('ou')
            logger.info("Found an ou: {}".format(ou))
            if ou.startswith('/'):
                new_accounts += expand_path(account, client)
            else:
                new_accounts += expand_ou(account, client)

    logger.debug(new_accounts)

    for parameter_name, parameter_details in new_manifest.get('parameters', {}).items():
        if parameter_details.get('macro'):
            macro_to_run = macros.get(parameter_details.get('macro').get('method'))
            result = macro_to_run(client, parameter_details.get('macro').get('args'))
            parameter_details['default'] = result
            del parameter_details['macro']

    for first_account in new_accounts:
        for parameter_name, parameter_details in first_account.get('parameters', {}).items():
            if parameter_details.get('macro'):
                macro_to_run = macros.get(parameter_details.get('macro').get('method'))
                result = macro_to_run(client, parameter_details.get('macro').get('args'))
                parameter_details['default'] = result
                del parameter_details['macro']

        times_seen = 0
        for second_account in new_accounts:
            if first_account.get('account_id') == second_account.get('account_id'):
                times_seen += 1
                if times_seen > 1:
                    message = "{} has been seen twice.".format(first_account.get('account_id'))
                    if first_account.get('expanded_from'):
                        message += "  It was included due to it being in the ou: {}".format(
                            first_account.get('expanded_from')
                        )
                    if second_account.get('expanded_from'):
                        message += "  It was included due to it being in the ou: {}".format(
                            second_account.get('expanded_from')
                        )
                    raise Exception(message)

    for launch_name, launch_details in new_manifest.get('launches').items():
        for parameter_name, parameter_details in launch_details.get('parameters', {}).items():
            if parameter_details.get('macro'):
                macro_to_run = macros.get(parameter_details.get('macro').get('method'))
                result = macro_to_run(client, parameter_details.get('macro').get('args'))
                parameter_details['default'] = result
                del parameter_details['macro']

    return new_manifest


VERSION = pkg_resources.require("aws-service-catalog-puppet")[0].version
template_dir = resolve_from_site_packages('templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    extensions=['jinja2.ext.do'],
)