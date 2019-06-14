import logging
import time
import os

import click
import yaml

from servicecatalog_puppet import constants
from betterboto import client as betterboto_client

logger = logging.getLogger(__file__)


def terminate_if_status_is_not_available(
        service_catalog, provisioned_product_name, product_id, account_id, region
):
    logger.info(f"[{provisioned_product_name}] {account_id}:{region} :: checking if should be terminated")
    # TODO - change to name query?
    response = service_catalog.search_provisioned_products(
        Filters={'SearchQuery': [
            "productId:{}".format(product_id)
        ]}
    )
    provisioned_product_id = False
    provisioning_artifact_id = False
    for r in response.get('ProvisionedProducts', []):
        if r.get('Name') == provisioned_product_name:
            current_status = r.get('Status')
            if current_status in ["AVAILABLE", "TAINTED"]:
                provisioned_product_id = r.get('Id')
                provisioning_artifact_id = r.get('ProvisioningArtifactId')
            elif current_status in ["UNDER_CHANGE", "PLAN_IN_PROGRESS"]:
                logger.info(f"[{provisioned_product_name}] {account_id}:{region} :: current status is {current_status}")
                while True:
                    status = service_catalog.describe_provisioned_product(
                        Id=r.get('Id')
                    ).get('ProvisionedProductDetail').get('Status')
                    logger.info(f"[{provisioned_product_name}] {account_id}:{region} :: waiting to complete: {status}")
                    time.sleep(5)
                    if status not in ["UNDER_CHANGE", "PLAN_IN_PROGRESS"]:
                        return terminate_if_status_is_not_available(
                            service_catalog, provisioned_product_name, product_id, account_id, region
                        )

            elif current_status == 'ERROR':
                logger.info(f"[{provisioned_product_name}] {account_id}:{region} :: terminating as its status is {r.get('Status')}")
                service_catalog.terminate_provisioned_product(
                    ProvisionedProductId=r.get('Id')
                )
                logger.info(f"[{provisioned_product_name}] {account_id}:{region} :: waiting for termination")
                while True:
                    response = service_catalog.search_provisioned_products(
                        Filters={
                            'SearchQuery': [f'name:{provisioned_product_name}']
                        }
                    )
                    if len(response.get('ProvisionedProducts')) > 0:
                        time.sleep(5)
                    else:
                        break
    logger.info(f"[{provisioned_product_name}] {account_id}:{region} :: Finished waiting for termination")
    return provisioned_product_id, provisioning_artifact_id


def get_stack_output_for(cloudformation, stack_name):
    logger.info(f"Getting stack output for {stack_name}")
    return cloudformation.describe_stacks(StackName=stack_name).get('Stacks')[0]


def get_default_parameters_for_stack(cloudformation, stack_name):
    logger.info(f"Getting default parameters for for {stack_name}")
    existing_stack_params_dict = {}
    #errored
    summary_response = cloudformation.get_template_summary(
        StackName=stack_name,
    )
    for parameter in summary_response.get('Parameters'):
        existing_stack_params_dict[parameter.get('ParameterKey')] = parameter.get('DefaultValue')
    return existing_stack_params_dict


def get_parameters_for_stack(cloudformation, stack_name):
    existing_stack_params_dict = get_default_parameters_for_stack(cloudformation, stack_name)

    logger.info(f"Getting parameters for for {stack_name}")
    stack = get_stack_output_for(cloudformation, stack_name)
    for stack_param in stack.get('Parameters', []):
        existing_stack_params_dict[stack_param.get('ParameterKey')] = stack_param.get('ParameterValue')
    return existing_stack_params_dict


def provision_product(
        service_catalog,
        launch_name,
        account_id,
        region,
        product_id,
        provisioning_artifact_id,
        puppet_account_id,
        path_id,
        params,
        version,
):
    stack_name = "-".join([constants.PREFIX, account_id, region, launch_name])
    logger.info(f"[{launch_name}] {account_id}:{region} :: Creating a plan")
    regional_sns_topic = f"arn:aws:sns:{region}:{puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
    provisioning_parameters = []
    for p in params.keys():
        provisioning_parameters.append({
            'Key': p,
            'Value': params.get(p),
        })
    response = service_catalog.create_provisioned_product_plan(
        PlanName=stack_name,
        PlanType='CLOUDFORMATION',
        PathId=path_id,
        ProductId=product_id,
        ProvisionedProductName=launch_name,
        ProvisioningArtifactId=provisioning_artifact_id,
        ProvisioningParameters=provisioning_parameters,
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
            regional_sns_topic,
        ],
    )
    logger.info(f"[{launch_name}] {account_id}:{region} :: Plan created, waiting for completion")

    plan_id = response.get('PlanId')
    plan_status = 'CREATE_IN_PROGRESS'

    while plan_status == 'CREATE_IN_PROGRESS':
        response = service_catalog.describe_provisioned_product_plan(
            PlanId=plan_id
        )
        plan_status = response.get('ProvisionedProductPlanDetails').get('Status')
        logger.info(f"[{launch_name}] {account_id}:{region} :: Waiting for product plan: {plan_status}")
        time.sleep(5)

    if plan_status == 'CREATE_SUCCESS':
        logger.info(
            f"[{launch_name}] {account_id}:{region} :: Plan created, "
            f"changes: {yaml.safe_dump(response.get('ResourceChanges'))}"
        )
        if len(response.get('ResourceChanges')) == 0:
            logger.warning(f"[{launch_name}] {account_id}:{region} :: There are no resource changes in this plan, "
                        f"running this anyway - your product will be marked as tainted as your CloudFormation changeset"
                        f"will fail but your product will be the correct version and in tact.")


        logger.info(f"[{launch_name}] {account_id}:{region} :: executing changes")
        service_catalog.execute_provisioned_product_plan(PlanId=plan_id)
        execute_status = 'EXECUTE_IN_PROGRESS'
        while execute_status == 'EXECUTE_IN_PROGRESS':
            response = service_catalog.describe_provisioned_product_plan(
                PlanId=plan_id
            )
            logger.info(f"[{launch_name}] {account_id}:{region} :: executing changes for plan: {plan_id}")
            execute_status = response.get('ProvisionedProductPlanDetails').get('Status')
            logger.info(f"[{launch_name}] {account_id}:{region} :: waiting for execution to complete: {execute_status}")
            time.sleep(5)

        if execute_status == 'CREATE_SUCCESS':
            provisioned_product_id = response.get('ProvisionedProductPlanDetails').get('ProvisionProductId')

            logger.info(f"[{launch_name}] {account_id}:{region} :: waiting for change to complete")
            while True:
                response = service_catalog.describe_provisioned_product(
                    Id=provisioned_product_id
                )
                logger.info(
                    f"[{launch_name}] {account_id}:{region} :: "
                    f"waiting for change to complete: {response.get('ProvisionedProductDetail').get('Status')}"
                )
                execute_status = response.get('ProvisionedProductDetail').get('Status')
                if execute_status in ['AVAILABLE', 'TAINTED']:
                    break
                elif execute_status ==  'ERROR':
                    raise Exception(f"[{launch_name}] {account_id}:{region} :: Execute failed: {execute_status}")
                else:
                    time.sleep(5)

            service_catalog.delete_provisioned_product_plan(PlanId=plan_id)
            return provisioned_product_id

        else:
            raise Exception(f"[{launch_name}] {account_id}:{region} :: Execute failed: {execute_status}")

    else:
        raise Exception(f"[{launch_name}] {account_id}:{region} :: "
                     f"Plan failed: {response.get('ProvisionedProductPlanDetails').get('StatusMessage')}")


def get_path_for_product(service_catalog, product_id):
    logger.info(f'Getting path for product {product_id}')
    response = service_catalog.list_launch_paths(ProductId=product_id)
    if len(response.get('LaunchPathSummaries')) != 1:
        raise Exception("Found unexpected amount of LaunchPathSummaries")
    path_id = response.get('LaunchPathSummaries')[0].get('Id')
    logger.info(f'Got path: {path_id} for product: {product_id}')
    return path_id


def ensure_is_terminated(
        service_catalog, provisioned_product_name, product_id
):
    logger.info(f"Ensuring {provisioned_product_name} is terminated")
    response = service_catalog.search_provisioned_products(
        Filters={'SearchQuery': [
            "productId:{}".format(product_id)
        ]}
    )
    provisioned_product_id = False
    provisioning_artifact_id = False
    for r in response.get('ProvisionedProducts', []):
        if r.get('Name') == provisioned_product_name:
            provisioned_product_id = r.get('Id')
            provisioning_artifact_id = r.get('ProvisioningArtifactId')

            if r.get('Status') != "TERMINATED":
                logger.info(f"Terminating {provisioned_product_name}, its status is: {r.get('Status')}")
                service_catalog.terminate_provisioned_product(
                    ProvisionedProductId=r.get('Id')
                )
                logger.info(f"Waiting for termination of {provisioned_product_name}")
                while True:
                    response = service_catalog.search_provisioned_products(
                        Filters={
                            'SearchQuery': [f'name:{provisioned_product_name}']
                        }
                    )
                    if len(response.get('ProvisionedProducts')) > 0:
                        time.sleep(5)
                    else:
                        break
            else:
                logger.info(f"Skipping terminated launch: {provisioned_product_name}")

    logger.info(f"Finished ensuring {provisioned_product_name} is terminated")
    return provisioned_product_id, provisioning_artifact_id


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


def get_portfolio_for(portfolio_name, account_id, region):
    logger.info(f"Getting portfolio id for: {portfolio_name}")
    role = f"arn:aws:iam::{account_id}:role/servicecatalog-puppet/PuppetRole"
    with betterboto_client.CrossAccountClientContextManager(
            'servicecatalog', role, "-".join([account_id, region]), region_name=region
    ) as cross_account_servicecatalog:
        portfolio = None
        while True:
            response = cross_account_servicecatalog.list_accepted_portfolio_shares()
            assert response.get('NextPageToken') is None, "Pagination not supported"
            for portfolio_detail in response.get('PortfolioDetails'):
                if portfolio_detail.get('DisplayName') == portfolio_name:
                    portfolio = portfolio_detail
                    break

            if portfolio is None:
                response = cross_account_servicecatalog.list_portfolios()
                for portfolio_detail in response.get('PortfolioDetails', []):
                    if portfolio_detail.get('DisplayName') == portfolio_name:
                        portfolio = portfolio_detail
                        break

            assert portfolio is not None, "Could not find portfolio"
            logger.info(f"Found portfolio: {portfolio}")
            return portfolio


def ensure_portfolio(service_catalog, portfolio_name, provider_name, description=None):
    return find_portfolio(service_catalog, portfolio_name) \
           or create_portfolio(service_catalog, portfolio_name, provider_name, description)


def find_portfolio(service_catalog, portfolio_searching_for):
    logger.info('Searching for portfolio for: {}'.format(portfolio_searching_for))
    response = service_catalog.list_portfolios_single_page()
    for detail in response.get('PortfolioDetails'):
        if detail.get('DisplayName') == portfolio_searching_for:
            logger.info('Found portfolio: {}'.format(portfolio_searching_for))
            return detail
    return False


def create_portfolio(service_catalog, portfolio_name, provider_name, description=None):
    logger.info(f'Creating portfolio: {portfolio_name}')
    args = {
        'DisplayName': portfolio_name,
        'ProviderName': provider_name,
    }
    if description is not None:
        args['Description'] = description
    return service_catalog.create_portfolio(
        **args
    ).get('PortfolioDetail')


def run_pipeline(pipeline_name, tail):
    with betterboto_client.ClientContextManager('codepipeline') as codepipeline:
        pipeline_execution_id = codepipeline.start_pipeline_execution(name=pipeline_name).get('pipelineExecutionId')
        click.echo(
            f"https://{os.environ.get('AWS_DEFAULT_REGION')}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline_name}/executions/{pipeline_execution_id}/timeline"
        )
        if tail:
            while True:
                pipeline_execution = codepipeline.get_pipeline_execution(
                    pipelineName=pipeline_name,
                    pipelineExecutionId=pipeline_execution_id
                ).get('pipelineExecution')
                status = pipeline_execution.get('status')
                click.echo(f"status: {status}")
                if status != 'InProgress':
                    break
                else:
                    time.sleep(5)
        return pipeline_execution_id
