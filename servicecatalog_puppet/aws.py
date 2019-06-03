import logging
import time
import yaml

from servicecatalog_puppet.constants import PREFIX

logger = logging.getLogger(__file__)


def terminate_if_status_is_not_available(
        service_catalog, provisioned_product_name, product_id
):
    logger.info(f"Checking if {provisioned_product_name} should be terminated")
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
            if r.get('Status') == "AVAILABLE":
                provisioned_product_id = r.get('Id')
                provisioning_artifact_id = r.get('ProvisioningArtifactId')
            else:
                logger.info(f"Terminating {provisioned_product_name} as its status is {r.get('Status')}")
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
    logger.info(f"Finished checking if {provisioned_product_name} should be terminated")
    return provisioned_product_id, provisioning_artifact_id


def get_stack_output_for(cloudformation, stack_name):
    logger.info(f"Getting stack output for {stack_name}")
    return cloudformation.describe_stacks(StackName=stack_name).get('Stacks')[0]


def get_parameters_for_stack(cloudformation, stack_name):
    logger.info(f"Getting parameters for for {stack_name}")
    stack = get_stack_output_for(cloudformation, stack_name)
    existing_stack_params_dict = {}
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
    stack_name = "-".join([PREFIX, account_id, region, launch_name])
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
        logger.info('Waiting for product plan: {}'.format(plan_status))
        time.sleep(5)

    if plan_status == 'CREATE_SUCCESS':
        logger.info(
            f"[{launch_name}] {account_id}:{region} :: Plan created, "
            f"changes: {yaml.safe_dump(response.get('ResourceChanges'))}"
        )
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
                if execute_status in ['AVAILABLE', 'TAINTED', 'ERROR']:
                    break
                else:
                    time.sleep(5)

            service_catalog.delete_provisioned_product_plan(PlanId=plan_id)
            return provisioned_product_id

        else:
            logger.error(f"[{launch_name}] {account_id}:{region} :: Execute failed: {execute_status}")
            return False

    else:
        logger.error(f"[{launch_name}] {account_id}:{region} :: "
                     f"Plan failed: {response.get('ProvisionedProductPlanDetails').get('StatusMessage')}")
        return False


def get_path_for_product(service_catalog, product_id):
    logger.info(f'Getting path for product {product_id}')
    response = service_catalog.list_launch_paths(ProductId=product_id)
    if len(response.get('LaunchPathSummaries')) != 1:
        raise Exception("Found unexpected amount of LaunchPathSummaries")
    path_id = response.get('LaunchPathSummaries')[0].get('Id')
    logger.info(f'Got path: {path_id} for product: {product_id}')
    return path_id
