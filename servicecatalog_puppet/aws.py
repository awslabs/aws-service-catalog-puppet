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
                logger.info("Waiting for termination")
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


def get_parameters_for_stack(cloudformation, stack_name):
    stack = cloudformation.describe_stacks(StackName=stack_name).get('Stacks')[0]
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
    logger.info('Creating plan, params: {}'.format(params))
    regional_sns_topic = f"arn:aws:sns:{region}:{puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
    logger.info("regional_sns_topic is: {}".format(regional_sns_topic))
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
        pass
    else:
        raise Exception("Execute was not successful: {}".format(execute_status))
    service_catalog.delete_provisioned_product_plan(PlanId=plan_id)
