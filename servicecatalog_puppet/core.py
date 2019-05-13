import logging
import os
import time
from threading import Thread

import yaml
from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

from servicecatalog_puppet.asset_helpers import resolve_from_site_packages
from servicecatalog_puppet.constants import HOME_REGION_PARAM_NAME, CONFIG_PARAM_NAME, CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN, TEMPLATES, PREFIX

logger = logging.getLogger()


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
            sharing_policies = generate_bucket_policies_for_shares(deployment_map, puppet_account_id)
            write_share_template(portfolio_use_by_account, region, host_account_id, sharing_policies)


def deploy_launches(deployment_map, parameters, single_account, puppet_account_id):
    logger.info('Deploying launches')
    first_run_stream = {}
    second_run_stream = {}
    dependency_names = []
    for account_id, deployments in deployment_map.items():
        if single_account is None or account_id == single_account:
            for launch_name, launch_details in deployments.get('launches').items():
                for region in launch_details.get('regions', []):
                    stream_name = "{}/{}".format(account_id, region)
                    has_dependency = launch_details.get('depends_on') is not None
                    logger.info(
                        "{} has dependencies: {}, {}".format(
                            launch_details.get('launch_name'),
                            has_dependency,
                            launch_details.get('depends_on')
                        )
                    )
                    dependency_names += launch_details.get('depends_on', [])
                    if has_dependency:
                        if second_run_stream.get(stream_name) is None:
                            second_run_stream[stream_name] = []
                        second_run_stream[stream_name].append(launch_details)
                    else:
                        if first_run_stream.get(stream_name) is None:
                            first_run_stream[stream_name] = []
                        first_run_stream[stream_name].append(launch_details)

    logger.info("Launches that are dependencies: {}".format(dependency_names))
    for dependency in dependency_names:
        for stream_name, launch_details_list in first_run_stream.items():
            for launch_detail in launch_details_list:
                if launch_detail.get('launch_name') == dependency:
                    launch_detail['should_wait_for_cloudformation'] = True

    deploy_stream(
        "first_run_stream",
        first_run_stream,
        parameters,
        puppet_account_id,
        deployment_map
    )
    deploy_stream(
        "second_run_stream",
        second_run_stream,
        parameters,
        puppet_account_id,
        deployment_map
    )


def deploy_stream(streams_name, streams, parameters, puppet_account_id, deployment_map):
    logger.info("deploying streams: {}".format(streams_name))
    threads = []
    for stream_name, stream_detail in streams.items():
        process = Thread(
            name=stream_name,
            target=process_stream,
            args=[stream_name, stream_detail, parameters, puppet_account_id, deployment_map]
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
            if r.get('Status') == "AVAILABLE":
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
        params,
        version,
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
            },
            {
                'Key': 'version',
                'Value': version,
            },
        ],
        NotificationArns=[
            "arn:aws:sns:{}:{}:servicecatalog-puppet-cloudformation-events".format(
                get_home_region(),
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
        logger.info("plan_id is: {}".format(plan_id))
        execute_status = response.get('ProvisionedProductPlanDetails').get('Status')
        logger.info('Waiting for execute: {}'.format(execute_status))
        time.sleep(5)

    if execute_status == 'CREATE_SUCCESS':
        provision_product_id = response.get('ProvisionedProductPlanDetails').get('ProvisionProductId')
        stack_name = "SC-{}-{}".format(account, provision_product_id)
        role = "arn:aws:iam::{}:role/{}".format(account, 'servicecatalog-puppet/PuppetRole')
        with betterboto_client.CrossAccountClientContextManager(
                        'cloudformation', role, 'xross', region_name=region
        ) as cloudformation:
            if launch.get('outputs', {}).get('ssm') is not None or launch.get('should_wait_for_cloudformation'):
                logger.info("Need to wait for stack completion")
                waiter = cloudformation.get_waiter('stack_create_complete')
                waiter.wait(StackName=stack_name)
                logger.info("Stack is now completed, continuing")

            if launch.get('outputs', {}).get('ssm') is not None:
                logger.info("There are ssm outputs that need processing")
                for outputs in launch.get('outputs', {}).get('ssm', []):
                    ssm_param_name = outputs.get('param_name')
                    ssm_param_value = outputs.get('stack_output')
                    ssm_param_region = outputs.get('region', get_home_region())
                    logger.info('Trying to set SSM parameter: {}'.format(ssm_param_name))
                    logger.info(('Looking for stack: {}'.format(stack_name)))
                    stack_response = cloudformation.describe_stacks(
                        StackName=stack_name
                    )
                    if len(stack_response.get('Stacks')) != 1:
                        raise Exception("Found more or less than 1 stack with the name: {}".format(
                            stack_name
                        ))
                    stack = stack_response.get('Stacks')[0]
                    logger.info(('Looking for output: {} in: {}'.format(ssm_param_value, stack.get('Outputs', []))))
                    for stack_output in stack.get('Outputs', []):
                        if stack_output.get('OutputKey') == ssm_param_value:
                            logger.info('Adding SSM parameter: {} of value: {} in region: {}'.format(
                                ssm_param_name, stack_output.get('OutputValue'), ssm_param_region
                            ))
                            with betterboto_client.ClientContextManager('ssm', region_name=ssm_param_region) as ssm:
                                ssm.put_parameter(
                                    Name=ssm_param_name,
                                    Value=stack_output.get('OutputValue'),
                                    Description=stack_output.get('Description', ''),
                                    Type='String',
                                    Tags=[
                                        {
                                            "Key": "SourceStackName",
                                            "Value": stack_name,
                                        },
                                        {
                                            "Key": "SourceStackOutputName",
                                            "Value": ssm_param_value,
                                        },
                                        {
                                            "Key": "SourceStackId",
                                            "Value": stack.get('StackId'),
                                        },
                                    ]
                                )
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
            'servicecatalog', role, stream_name.replace("/", "-"), region_name=region
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
                    launch.get('version'),
                )

    logger.info('Finished creating stacks')


template_dir = resolve_from_site_packages('templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    extensions=['jinja2.ext.do'],
)