import logging
import time
import os

import click
import yaml

from servicecatalog_puppet import constants
from betterboto import client as betterboto_client

logger = logging.getLogger(__file__)


def terminate_provisioned_product(prefix, service_catalog, provisioned_product_id):
    logger.info(f"{prefix} :: about to terminate {provisioned_product_id}")
    record_detail = service_catalog.terminate_provisioned_product(
        ProvisionedProductId=provisioned_product_id
    ).get("RecordDetail")
    record_id = record_detail.get("RecordId")

    logger.info(
        f"{prefix} :: waiting for termination of {provisioned_product_id} to complete"
    )
    status = "IN_PROGRESS"
    while status == "IN_PROGRESS":
        record_detail = service_catalog.describe_record(Id=record_id).get(
            "RecordDetail"
        )
        status = record_detail.get("Status")
        logger.info(
            f"{prefix} :: termination of {provisioned_product_id} current status: {status}"
        )
        if status != "IN_PROGRESS":
            break
        else:
            time.sleep(3)

    if status not in ["CREATED", "SUCCEEDED"]:
        logger.info(yaml.safe_dump(record_detail.get("RecordErrors")))
        raise Exception(f"Failed to terminate provisioned product: Status = {status}")


def terminate_if_status_is_not_available(
    service_catalog, provisioned_product_name, product_id, account_id, region
):
    prefix = f"[{provisioned_product_name}] {account_id}:{region}"
    logger.info(f"{prefix} :: checking if should be terminated")
    response = service_catalog.scan_provisioned_products_single_page(
        AccessLevelFilter={"Key": "Account", "Value": "self"},
    )
    provisioned_product_id = False
    provisioning_artifact_id = False
    for r in response.get("ProvisionedProducts", []):
        if r.get("Name") == provisioned_product_name:
            current_status = r.get("Status")
            if current_status in ["AVAILABLE", "TAINTED"]:
                provisioned_product_id = r.get("Id")
                provisioning_artifact_id = r.get("ProvisioningArtifactId")
            elif current_status in ["UNDER_CHANGE", "PLAN_IN_PROGRESS"]:
                logger.info(f"{prefix} :: current status is {current_status}")
                while True:
                    status = (
                        service_catalog.describe_provisioned_product(Id=r.get("Id"))
                        .get("ProvisionedProductDetail")
                        .get("Status")
                    )
                    logger.info(f"{prefix} :: waiting to complete: {status}")
                    time.sleep(5)
                    if status not in ["UNDER_CHANGE", "PLAN_IN_PROGRESS"]:
                        return terminate_if_status_is_not_available(
                            service_catalog,
                            provisioned_product_name,
                            product_id,
                            account_id,
                            region,
                        )

            elif current_status == "ERROR":
                logger.info(
                    f"{prefix} :: terminating as its status is {r.get('Status')}"
                )
                terminate_provisioned_product(prefix, service_catalog, r.get("Id"))
    logger.info(f"{prefix} :: Finished waiting for termination")
    return provisioned_product_id, provisioning_artifact_id


def get_stack_output_for(cloudformation, stack_name):
    logger.info(f"Getting stack output for {stack_name}")
    return cloudformation.describe_stacks(StackName=stack_name).get("Stacks")[0]


def get_default_parameters_for_stack(cloudformation, stack_name):
    logger.info(f"Getting default parameters for for {stack_name}")
    existing_stack_params_dict = {}
    summary_response = cloudformation.get_template_summary(StackName=stack_name,)
    for parameter in summary_response.get("Parameters"):
        existing_stack_params_dict[parameter.get("ParameterKey")] = parameter.get(
            "DefaultValue"
        )
    return existing_stack_params_dict


def get_parameters_for_stack(cloudformation, stack_name):
    existing_stack_params_dict = get_default_parameters_for_stack(
        cloudformation, stack_name
    )

    stack = get_stack_output_for(cloudformation, stack_name)
    for stack_param in stack.get("Parameters", []):
        existing_stack_params_dict[stack_param.get("ParameterKey")] = stack_param.get(
            "ParameterValue"
        )
    return existing_stack_params_dict


def provision_product_with_plan(
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
    should_use_sns,
):
    uid = f"[{launch_name}] {account_id}:{region}]"
    stack_name = "-".join([constants.PREFIX, account_id, region, launch_name])
    logger.info(f"{uid} :: Checking for an existing plan")
    if puppet_account_id == account_id:
        provisioned_product_plans = service_catalog.list_provisioned_product_plans_single_page().get(
            "ProvisionedProductPlans", []
        )
    else:
        provisioned_product_plans = service_catalog.list_provisioned_product_plans_single_page(
            AccessLevelFilter={"Key": "Account", "Value": "self"}
        ).get(
            "ProvisionedProductPlans", []
        )
    for provisioned_product_plan in provisioned_product_plans:
        logger.info(
            f"{uid} :: Found plan for {provisioned_product_plan.get('ProvisionProductName')}"
        )
        if provisioned_product_plan.get("ProvisionProductName") == launch_name:
            f"{uid} :: Found existing plan, going to terminate it"
            service_catalog.delete_provisioned_product_plan(
                PlanId=provisioned_product_plan.get("PlanId")
            )

    logger.info(f"{uid} :: Creating a plan")
    regional_sns_topic = f"arn:aws:sns:{region}:{puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
    provisioning_parameters = []
    for p in params.keys():
        provisioning_parameters.append(
            {"Key": p, "Value": params.get(p),}
        )
    response = service_catalog.create_provisioned_product_plan(
        PlanName=stack_name,
        PlanType="CLOUDFORMATION",
        PathId=path_id,
        ProductId=product_id,
        ProvisionedProductName=launch_name,
        ProvisioningArtifactId=provisioning_artifact_id,
        ProvisioningParameters=provisioning_parameters,
        Tags=[
            {"Key": "ServiceCatalogPuppet:Actor", "Value": "Generated",},
            {"Key": "launch_name", "Value": launch_name,},
            {"Key": "version", "Value": version,},
        ],
        NotificationArns=[regional_sns_topic,] if should_use_sns else [],
    )
    logger.info(f"{uid} :: Plan created, waiting for completion")

    plan_id = response.get("PlanId")
    plan_status = "CREATE_IN_PROGRESS"

    while plan_status == "CREATE_IN_PROGRESS":
        response = service_catalog.describe_provisioned_product_plan(PlanId=plan_id)
        plan_status = response.get("ProvisionedProductPlanDetails").get("Status")
        logger.info(f"{uid} :: Waiting for product plan: {plan_status}")
        time.sleep(5)

    if plan_status in ["CREATE_SUCCESS", "EXECUTE_SUCCESS"]:
        logger.info(
            f"{uid} :: Plan created, "
            f"changes: {yaml.safe_dump(response.get('ResourceChanges'))}"
        )
        if len(response.get("ResourceChanges")) == 0:
            logger.warning(
                f"{uid} :: There are no resource changes in this plan, "
                f"running this anyway - your product will be marked as tainted as your CloudFormation changeset"
                f"will fail but your product will be the correct version and in tact."
            )

        logger.info(f"{uid} :: executing changes")
        service_catalog.execute_provisioned_product_plan(PlanId=plan_id)

        plan_execute_status = "EXECUTE_IN_PROGRESS"
        while plan_execute_status == "EXECUTE_IN_PROGRESS":
            response = service_catalog.describe_provisioned_product_plan(PlanId=plan_id)
            logger.info(f"{uid} :: executing changes for plan: {plan_id}")
            plan_execute_status = response.get("ProvisionedProductPlanDetails").get(
                "Status"
            )
            logger.info(
                f"{uid} :: waiting for execution to complete: {plan_execute_status}"
            )
            time.sleep(5)

        if plan_execute_status in ["CREATE_SUCCESS", "EXECUTE_SUCCESS"]:
            provisioned_product_id = response.get("ProvisionedProductPlanDetails").get(
                "ProvisionProductId"
            )

            logger.info(f"{uid} :: waiting for change to complete")
            while True:
                response = service_catalog.describe_provisioned_product(
                    Id=provisioned_product_id
                )
                logger.info(
                    f"{uid} :: "
                    f"waiting for provision to complete: {response.get('ProvisionedProductDetail').get('Status')}"
                )
                provisioned_product_detail = response.get("ProvisionedProductDetail")
                execute_status = provisioned_product_detail.get("Status")
                if execute_status in ["AVAILABLE", "TAINTED", "EXECUTE_SUCCESS"]:
                    break
                elif execute_status == "ERROR":
                    raise Exception(
                        f"{uid} :: Execute failed: {execute_status}: {provisioned_product_detail.get('StatusMessage')}"
                    )
                else:
                    time.sleep(5)

            service_catalog.delete_provisioned_product_plan(PlanId=plan_id)
            return provisioned_product_id

        else:
            raise Exception(f"{uid} :: Plan execute failed: {plan_execute_status}")

    else:
        raise Exception(
            f"{uid} :: Plan failed: {response.get('ProvisionedProductPlanDetails').get('StatusMessage')}"
        )


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
    should_use_sns,
    execution,
):
    uid = f"[{launch_name}] {account_id}:{region}]"
    provisioning_parameters = []
    for p in params.keys():
        provisioning_parameters.append(
            {"Key": p, "Value": params.get(p),}
        )
    provisioned_product_id = (
        service_catalog.provision_product(
            ProductId=product_id,
            ProvisioningArtifactId=provisioning_artifact_id,
            PathId=path_id,
            ProvisionedProductName=launch_name,
            ProvisioningParameters=provisioning_parameters,
            Tags=[
                {"Key": "ServiceCatalogPuppet:Actor", "Value": "Generated",},
                {"Key": "launch_name", "Value": launch_name,},
                {"Key": "version", "Value": version,},
            ],
            NotificationArns=[
                f"arn:aws:sns:{region}:{puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events",
            ]
            if should_use_sns
            else [],
        )
        .get("RecordDetail")
        .get("ProvisionedProductId")
    )
    logger.info(f"{uid}: provisioning started: {provisioned_product_id}")

    if execution == constants.EXECUTION_MODE_ASYNC:
        return provisioned_product_id
    else:
        while True:
            response = service_catalog.describe_provisioned_product(
                Id=provisioned_product_id
            )
            logger.info(
                f"{uid} :: "
                f"waiting for provision to complete: {response.get('ProvisionedProductDetail').get('Status')}"
            )
            provisioned_product_detail = response.get("ProvisionedProductDetail")
            execute_status = provisioned_product_detail.get("Status")
            if execute_status in ["AVAILABLE", "TAINTED", "EXECUTE_SUCCESS"]:
                break
            elif execute_status == "ERROR":
                raise Exception(
                    f"{uid} :: Execute failed: {execute_status}: {provisioned_product_detail.get('StatusMessage')}"
                )
            else:
                time.sleep(5)
        return provisioned_product_id


def update_provisioned_product(
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
    execution,
):
    uid = f"[{launch_name}] {account_id}:{region}]"
    provisioning_parameters = []
    for p in params.keys():
        provisioning_parameters.append(
            {"Key": p, "Value": params.get(p),}
        )
    provisioned_product_id = (
        service_catalog.update_provisioned_product(
            ProductId=product_id,
            ProvisioningArtifactId=provisioning_artifact_id,
            PathId=path_id,
            ProvisionedProductName=launch_name,
            ProvisioningParameters=provisioning_parameters,
        )
        .get("RecordDetail")
        .get("ProvisionedProductId")
    )
    logger.info(f"{uid}: provisioning started: {provisioned_product_id}")

    if execution == constants.EXECUTION_MODE_ASYNC:
        return provisioned_product_id
    else:
        while True:
            response = service_catalog.describe_provisioned_product(
                Id=provisioned_product_id
            )
            logger.info(
                f"{uid} :: "
                f"waiting for provision to complete: {response.get('ProvisionedProductDetail').get('Status')}"
            )
            provisioned_product_detail = response.get("ProvisionedProductDetail")
            execute_status = provisioned_product_detail.get("Status")
            if execute_status in ["AVAILABLE", "TAINTED", "EXECUTE_SUCCESS"]:
                break
            elif execute_status == "ERROR":
                raise Exception(
                    f"{uid} :: Execute failed: {execute_status}: {provisioned_product_detail.get('StatusMessage')}"
                )
            else:
                time.sleep(5)
        return provisioned_product_id


def get_path_for_product(service_catalog, product_id, portfolio_name):
    logger.info(f"Getting path for product {product_id}")
    response = service_catalog.list_launch_paths(ProductId=product_id)
    if len(response.get("LaunchPathSummaries")) == 1:
        path_id = response.get("LaunchPathSummaries")[0].get("Id")
        logger.info(f"There is only one path: {path_id} for product: {product_id}")
        return path_id
    else:
        for launch_path_summary in response.get("LaunchPathSummaries", []):
            name = launch_path_summary.get("Name")
            if name == portfolio_name:
                path_id = launch_path_summary.get("Id")
                logger.info(f"Got path: {path_id} for product: {product_id}")
                return path_id

    raise Exception("Failed to find a LaunchPath")


def ensure_is_terminated(service_catalog, provisioned_product_name, product_id):
    logger.info(f"Ensuring {provisioned_product_name} is terminated")
    r = get_provisioned_product_details(
        product_id, provisioned_product_name, service_catalog
    )

    if r is not None:
        provisioned_product_id = r.get("Id")
        provisioning_artifact_id = r.get("ProvisioningArtifactId")

        if r.get("Status") != "TERMINATED":
            logger.info(
                f"Terminating {provisioned_product_name}, its status is: {r.get('Status')}"
            )
            terminate_provisioned_product(
                f"{provisioned_product_name}:{product_id}", service_catalog, r.get("Id")
            )
        else:
            logger.info(f"Skipping terminated launch: {provisioned_product_name}")

        logger.info(f"Finished ensuring {provisioned_product_name} is terminated")
        return provisioned_product_id, provisioning_artifact_id
    else:
        return None, None


def get_provisioned_product_details(
    product_id, provisioned_product_name, service_catalog
):
    response = service_catalog.scan_provisioned_products_single_page(
        AccessLevelFilter={"Key": "Account", "Value": "self"},
    )
    for r in response.get("ProvisionedProducts", []):
        if r.get("Name") == provisioned_product_name:
            return r
    return None


def get_provisioning_artifact_id_for(
    portfolio_name, product_name, version_name, account_id, region
):
    logger.info(
        "Getting provisioning artifact id for: {} {} {} in the region: {} of account: {}".format(
            portfolio_name, product_name, version_name, region, account_id
        )
    )
    role = "arn:aws:iam::{}:role/{}".format(
        account_id, "servicecatalog-puppet/PuppetRole"
    )
    with betterboto_client.CrossAccountClientContextManager(
        "servicecatalog", role, "-".join([account_id, region]), region_name=region
    ) as cross_account_servicecatalog:
        product_id = None
        version_id = None
        portfolio_id = None

        response = cross_account_servicecatalog.list_accepted_portfolio_shares()
        assert response.get("NextPageToken") is None, "Pagination not supported"
        for portfolio_detail in response.get("PortfolioDetails"):
            if portfolio_detail.get("DisplayName") == portfolio_name:
                portfolio_id = portfolio_detail.get("Id")
                break

        if portfolio_id is None:
            response = cross_account_servicecatalog.list_portfolios_single_page()
            for portfolio_detail in response.get("PortfolioDetails", []):
                if portfolio_detail.get("DisplayName") == portfolio_name:
                    portfolio_id = portfolio_detail.get("Id")
                    break

        assert portfolio_id is not None, "Could not find portfolio"
        logger.info(
            f"Found portfolio: {portfolio_id}, looking for product: {product_name}"
        )

        response = cross_account_servicecatalog.search_products_as_admin_single_page(
            PortfolioId=portfolio_id
        )
        for product_view_details in response.get("ProductViewDetails"):
            product_view = product_view_details.get("ProductViewSummary")
            logging.info(f"looking at {product_view.get('Name')}")
            if product_view.get("Name") == product_name:
                logger.info("Found product: {}".format(product_view))
                product_id = product_view.get("ProductId")

        assert product_id is not None, "Did not find product looking for"

        response = cross_account_servicecatalog.list_provisioning_artifacts_single_page(
            ProductId=product_id
        )
        for provisioning_artifact_detail in response.get("ProvisioningArtifactDetails"):
            if provisioning_artifact_detail.get("Name") == version_name:
                version_id = provisioning_artifact_detail.get("Id")
        assert version_id is not None, "Did not find version looking for"
        return product_id, version_id


def ensure_portfolio(service_catalog, portfolio_name, provider_name, description=None):
    return find_portfolio(service_catalog, portfolio_name) or create_portfolio(
        service_catalog, portfolio_name, provider_name, description
    )


def find_portfolio(service_catalog, portfolio_searching_for):
    logger.info("Searching for portfolio for: {}".format(portfolio_searching_for))
    response = service_catalog.list_portfolios_single_page()
    for detail in response.get("PortfolioDetails"):
        if detail.get("DisplayName") == portfolio_searching_for:
            logger.info("Found portfolio: {}".format(portfolio_searching_for))
            return detail
    return False


def create_portfolio(service_catalog, portfolio_name, provider_name, description=None):
    logger.info(f"Creating portfolio: {portfolio_name}")
    args = {
        "DisplayName": portfolio_name,
        "ProviderName": provider_name,
    }
    if description is not None:
        args["Description"] = description
    return service_catalog.create_portfolio(**args).get("PortfolioDetail")


def run_pipeline(pipeline_name, tail):
    with betterboto_client.ClientContextManager("codepipeline") as codepipeline:
        pipeline_execution_id = codepipeline.start_pipeline_execution(
            name=pipeline_name
        ).get("pipelineExecutionId")
        click.echo(
            f"https://{os.environ.get('AWS_DEFAULT_REGION')}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline_name}/executions/{pipeline_execution_id}/timeline"
        )
        if tail:
            while True:
                pipeline_execution = codepipeline.get_pipeline_execution(
                    pipelineName=pipeline_name,
                    pipelineExecutionId=pipeline_execution_id,
                ).get("pipelineExecution")
                status = pipeline_execution.get("status")
                click.echo(f"status: {status}")
                if status != "InProgress":
                    break
                else:
                    time.sleep(5)
        return pipeline_execution_id


def get_version_id_for(servicecatalog, product_id, version_name):
    version_id = None
    response = servicecatalog.list_provisioning_artifacts_single_page(
        ProductId=product_id
    )
    for provisioning_artifact_detail in response.get("ProvisioningArtifactDetails"):
        if provisioning_artifact_detail.get("Name") == version_name:
            version_id = provisioning_artifact_detail.get("Id")
    assert version_id is not None, "Did not find version looking for"
    return version_id


def get_portfolio_for(servicecatalog, portfolio_name):
    result = None

    response = servicecatalog.list_accepted_portfolio_shares()
    assert response.get("NextPageToken") is None, "Pagination not supported"
    for portfolio_detail in response.get("PortfolioDetails"):
        if portfolio_detail.get("DisplayName") == portfolio_name:
            result = portfolio_detail
            break

    if result is None:
        response = servicecatalog.list_portfolios_single_page()
        for portfolio_detail in response.get("PortfolioDetails", []):
            if portfolio_detail.get("DisplayName") == portfolio_name:
                result = portfolio_detail
                break

    assert result is not None, "Could not find portfolio"
    return result


def get_portfolio_id_for(servicecatalog, portfolio_name):
    return get_portfolio_for(servicecatalog, portfolio_name).get("Id")
