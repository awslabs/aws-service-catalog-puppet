#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants


PER_REGION = "_{region}"
PER_REGION_OF_ACCOUNT = PER_REGION + "_OF_{account_id}"

CLOUDFORMATION_ENSURE_DELETED_PER_REGION_OF_ACCOUNT = (
    "CLOUDFORMATION_ENSURE_DELETED" + PER_REGION_OF_ACCOUNT
)
CLOUDFORMATION_GET_TEMPLATE_SUMMARY_PER_REGION_OF_ACCOUNT = (
    "CLOUDFORMATION_GET_TEMPLATE_SUMMARY" + PER_REGION_OF_ACCOUNT
)
CLOUDFORMATION_GET_TEMPLATE_PER_REGION_OF_ACCOUNT = (
    "CLOUDFORMATION_GET_TEMPLATE" + PER_REGION_OF_ACCOUNT
)
CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT = (
    "CLOUDFORMATION_CREATE_OR_UPDATE" + PER_REGION_OF_ACCOUNT
)
CLOUDFORMATION_LIST_STACKS_PER_REGION_OF_ACCOUNT = (
    "CLOUDFORMATION_LIST_STACKS" + PER_REGION_OF_ACCOUNT
)
CLOUDFORMATION_DESCRIBE_STACKS_PER_REGION_OF_ACCOUNT = (
    "CLOUDFORMATION_DESCRIBE_STACKS" + PER_REGION_OF_ACCOUNT
)

SERVICE_CATALOG_SCAN_PROVISIONED_PRODUCTS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_SCAN_PROVISIONED_PRODUCTS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_UPDATE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_UPDATE_PROVISIONED_PRODUCT" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_PROVISION_PRODUCT_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_PROVISION_PRODUCT" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_TERMINATE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_TERMINATE_PROVISIONED_PRODUCT" + PER_REGION_OF_ACCOUNT
)

SERVICE_CATALOG_TERMINATE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_TERMINATE_PROVISIONED_PRODUCT_PLAN" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_CREATE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_CREATE_PROVISIONED_PRODUCT_PLAN" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PLAN" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_EXECUTE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_EXECUTE_PROVISIONED_PRODUCT_PLAN" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DESCRIBE_RECORD_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DESCRIBE_RECORD" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_LIST_PROVISIONED_PRODUCT_PLANS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_LIST_PROVISIONED_PRODUCT_PLANS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_LIST_LAUNCH_PATHS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_LIST_LAUNCH_PATHS" + PER_REGION_OF_ACCOUNT
)

SERVICE_CATALOG_LIST_PRINCIPALS_FOR_PORTFOLIO_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_LIST_PRINCIPALS_FOR_PORTFOLIO" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DISASSOCIATE_PRINCIPAL_FROM_PORTFOLIO_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DISASSOCIATE_PRINCIPAL_FROM_PORTFOLIO" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_ASSOCIATE_PRINCIPAL_FROM_PORTFOLIO_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_ASSOCIATE_PRINCIPAL_FROM_PORTFOLIO" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_LIST_PORTFOLIOS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_LIST_PORTFOLIOS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DELETE_PORTFOLIOS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DELETE_PORTFOLIOS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_CREATE_PORTFOLIOS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_CREATE_PORTFOLIOS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_LIST_ACCEPTED_PORTFOLIO_SHARES_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_LIST_ACCEPTED_PORTFOLIO_SHARES" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_LIST_PORTFOLIO_ACCESS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_LIST_PORTFOLIO_ACCESS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE = "SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE"
SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE_PER_REGION = (
    "SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE" + PER_REGION
)
SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE_PER_REGION = (
    "SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE" + PER_REGION
)
SERVICE_CATALOG_DESCRIBE_PORTFOLIO_SHARE_STATUS_PER_REGION = (
    "SERVICE_CATALOG_DESCRIBE_PORTFOLIO_SHARE_STATUS" + PER_REGION
)
SERVICE_CATALOG_DESCRIBE_PORTFOLIO_SHARES_PER_REGION = (
    "SERVICE_CATALOG_DESCRIBE_PORTFOLIO_SHARES" + PER_REGION
)
SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_ACCEPT_PORTFOLIO_SHARE_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_ACCEPT_PORTFOLIO_SHARE" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_SEARCH_PRODUCTS_AS_ADMIN_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_SEARCH_PRODUCTS_AS_ADMIN" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DESCRIBE_PRODUCT_AS_ADMIN_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DESCRIBE_PRODUCT_AS_ADMIN" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DESCRIBE_PROVISIONING_ARTEFACT_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DESCRIBE_PROVISIONING_ARTEFACT" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DESCRIBE_PROVISIONING_PARAMETERS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DESCRIBE_PROVISIONING_PARAMETERS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_LIST_PROVISIONING_ARTIFACTS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_LIST_PROVISIONING_ARTIFACTS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_COPY_PRODUCT_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_COPY_PRODUCT" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_DESCRIBE_COPY_PRODUCT_STATUS_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_DESCRIBE_COPY_PRODUCT_STATUS" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_ASSOCIATE_PRODUCT_WITH_PORTFOLIO_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_ASSOCIATE_PRODUCT_WITH_PORTFOLIO" + PER_REGION_OF_ACCOUNT
)
SERVICE_CATALOG_UPDATE_PROVISIONING_ARTIFACT_PER_REGION_OF_ACCOUNT = (
    "SERVICE_CATALOG_UPDATE_PROVISIONING_ARTIFACT" + PER_REGION_OF_ACCOUNT
)

SSM_GET_PARAMETER_PER_REGION_OF_ACCOUNT = "SSM_GET_PARAMETER" + PER_REGION_OF_ACCOUNT
SSM_DELETE_PARAMETER_PER_REGION_OF_ACCOUNT = (
    "SSM_DELETE_PARAMETER" + PER_REGION_OF_ACCOUNT
)
SSM_PUT_PARAMETER_PER_REGION_OF_ACCOUNT = "SSM_PUT_PARAMETER" + PER_REGION_OF_ACCOUNT
SSM_GET_PARAMETER_BY_PATH_PER_REGION_OF_ACCOUNT = (
    "SSM_GET_PARAMETER_BY_PATH" + PER_REGION_OF_ACCOUNT
)


ORGANIZATIONS_ATTACH_POLICY_PER_REGION = "ORGANIZATIONS_ATTACH_POLICY" + PER_REGION
ORGANIZATIONS_DETACH_POLICY_PER_REGION = "ORGANIZATIONS_DETACH_POLICY" + PER_REGION
ORGANIZATIONS_LIST_POLICIES_PER_REGION = "ORGANIZATIONS_LIST_POLICIES" + PER_REGION
ORGANIZATIONS_CREATE_POLICIES_PER_REGION = "ORGANIZATIONS_CREATE_POLICIES" + PER_REGION
ORGANIZATIONS_DESCRIBE_POLICIES_PER_REGION = (
    "ORGANIZATIONS_DESCRIBE_POLICIES" + PER_REGION
)
ORGANIZATIONS_UPDATE_POLICIES_PER_REGION = "ORGANIZATIONS_UPDATE_POLICIES" + PER_REGION
ORGANIZATIONS_CREATE_OU = "ORGANIZATIONS_CREATE_POLICIES"

IAM_SIMULATE_POLICY_PER_REGION_OF_ACCOUNT = (
    "IAM_SIMULATE_POLICY_{simulation_type}" + PER_REGION_OF_ACCOUNT
)

LAMBDA_INVOKE_PER_REGION_OF_ACCOUNT = "LAMBDA_INVOKE" + PER_REGION_OF_ACCOUNT

CODEBUILD_START_BUILD_PER_REGION_OF_ACCOUNT = (
    "CODEBUILD_START_BUILD" + PER_REGION_OF_ACCOUNT
)
CODEBUILD_BATCH_GET_PROJECTS_PER_REGION_OF_ACCOUNT = (
    "CODEBUILD_BATCH_GET_PROJECTS_{project_name}" + PER_REGION_OF_ACCOUNT
)

CAN_ONLY_BE_RUN_ONCE_AT_A_TIME = "CAN_ONLY_BE_RUN_ONCE_AT_A_TIME"


def create(section_name, parameters_to_use, puppet_account_id):
    status = parameters_to_use.get("status")

    if section_name == constants.STACKS:
        if status == "terminated":
            resources = []
        else:
            resources = [
                CLOUDFORMATION_ENSURE_DELETED_PER_REGION_OF_ACCOUNT,
                CLOUDFORMATION_GET_TEMPLATE_SUMMARY_PER_REGION_OF_ACCOUNT,
                CLOUDFORMATION_GET_TEMPLATE_PER_REGION_OF_ACCOUNT,
                CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
            ]

            if parameters_to_use.get("launch_name") != "":
                resources.append(
                    SERVICE_CATALOG_SCAN_PROVISIONED_PRODUCTS_PER_REGION_OF_ACCOUNT
                    if "*" in parameters_to_use.get("launch_name")
                    else SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT
                )

            if parameters_to_use.get("stack_set_name") != "":
                resources.append(CLOUDFORMATION_LIST_STACKS_PER_REGION_OF_ACCOUNT)

    elif section_name == constants.LAUNCHES:
        if status == "terminated":
            resources = [
                SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_TERMINATE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_RECORD_PER_REGION_OF_ACCOUNT,
            ]
        else:
            resources = [
                SERVICE_CATALOG_SCAN_PROVISIONED_PRODUCTS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_TERMINATE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_RECORD_PER_REGION_OF_ACCOUNT,
                CLOUDFORMATION_GET_TEMPLATE_SUMMARY_PER_REGION_OF_ACCOUNT,
                CLOUDFORMATION_DESCRIBE_STACKS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_LIST_PROVISIONED_PRODUCT_PLANS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_TERMINATE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_CREATE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_EXECUTE_PROVISIONED_PRODUCT_PLAN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_UPDATE_PROVISIONED_PRODUCT_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_PROVISION_PRODUCT_PER_REGION_OF_ACCOUNT,
            ]
            if parameters_to_use.get("should_use_product_plans"):
                resources.append(
                    SERVICE_CATALOG_LIST_LAUNCH_PATHS_PER_REGION_OF_ACCOUNT,
                )

    elif section_name == constants.BOTO3_PARAMETERS:
        resources = []

    elif section_name == constants.SSM_PARAMETERS_WITH_A_PATH:
        resources = [
            SSM_GET_PARAMETER_BY_PATH_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.SSM_PARAMETERS:
        resources = [
            SSM_GET_PARAMETER_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.SSM_OUTPUTS:

        if parameters_to_use.get("status") == constants.TERMINATED:
            resources = [SSM_DELETE_PARAMETER_PER_REGION_OF_ACCOUNT]

        else:
            resources = [SSM_PUT_PARAMETER_PER_REGION_OF_ACCOUNT]

    elif section_name == constants.TAG_POLICIES:
        if status == "terminated":
            raise Exception(
                "No supported yet, raise a github issue if you would like to see this"
            )

        else:
            resources = [
                ORGANIZATIONS_ATTACH_POLICY_PER_REGION,
            ]

    elif section_name == constants.SERVICE_CONTROL_POLICIES:
        if status == "terminated":
            resources = [
                ORGANIZATIONS_DETACH_POLICY_PER_REGION,
            ]

        else:
            resources = [
                ORGANIZATIONS_ATTACH_POLICY_PER_REGION,
            ]

    elif section_name == constants.ASSERTIONS:
        resources = []

    elif section_name == constants.SIMULATE_POLICIES:
        resources = [IAM_SIMULATE_POLICY_PER_REGION_OF_ACCOUNT]

    elif section_name == constants.LAMBDA_INVOCATIONS:
        resources = [LAMBDA_INVOKE_PER_REGION_OF_ACCOUNT]

    elif section_name == constants.CODE_BUILD_RUNS:
        resources = [
            CODEBUILD_START_BUILD_PER_REGION_OF_ACCOUNT,
            CODEBUILD_BATCH_GET_PROJECTS_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.SPOKE_LOCAL_PORTFOLIOS:
        if status == "terminated":
            resources = [
                SERVICE_CATALOG_LIST_PORTFOLIOS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DELETE_PORTFOLIOS_PER_REGION_OF_ACCOUNT,
            ]

        else:
            resources = [
                SERVICE_CATALOG_LIST_PORTFOLIOS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_CREATE_PORTFOLIOS_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.PORTFOLIO_LOCAL:
        resources = [
            SERVICE_CATALOG_LIST_PORTFOLIOS_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.PORTFOLIO_IMPORTED:
        resources = [
            SERVICE_CATALOG_LIST_ACCEPTED_PORTFOLIO_SHARES_PER_REGION_OF_ACCOUNT
        ]

    elif section_name == constants.PORTFOLIO_ASSOCIATIONS:
        if status == "terminated":
            resources = [
                CLOUDFORMATION_ENSURE_DELETED_PER_REGION_OF_ACCOUNT,
            ]
        else:
            resources = [
                CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
                CLOUDFORMATION_DESCRIBE_STACKS_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.PORTFOLIO_CONSTRAINTS_LAUNCH:
        if status == "terminated":
            resources = [
                CLOUDFORMATION_ENSURE_DELETED_PER_REGION_OF_ACCOUNT,
            ]

        else:
            resources = [
                CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.PORTFOLIO_CONSTRAINTS_RESOURCE_UPDATE:
        if status == "terminated":
            resources = [
                CLOUDFORMATION_ENSURE_DELETED_PER_REGION_OF_ACCOUNT,
            ]

        else:
            resources = [
                CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.PORTFOLIO_COPY:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            resources = [
                SERVICE_CATALOG_SEARCH_PRODUCTS_AS_ADMIN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_LIST_PROVISIONING_ARTIFACTS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_COPY_PRODUCT_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_COPY_PRODUCT_STATUS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_ASSOCIATE_PRODUCT_WITH_PORTFOLIO_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_UPDATE_PROVISIONING_ARTIFACT_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.PORTFOLIO_IMPORT:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            resources = [
                SERVICE_CATALOG_SEARCH_PRODUCTS_AS_ADMIN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_LIST_PROVISIONING_ARTIFACTS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_ASSOCIATE_PRODUCT_WITH_PORTFOLIO_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.PORTFOLIO_SHARE_AND_ACCEPT_ACCOUNT:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            resources = [
                SERVICE_CATALOG_LIST_ACCEPTED_PORTFOLIO_SHARES_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_LIST_PORTFOLIO_ACCESS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_ACCEPT_PORTFOLIO_SHARE_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.PORTFOLIO_SHARE_AND_ACCEPT_AWS_ORGANIZATIONS:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            resources = [
                SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE,
                SERVICE_CATALOG_CREATE_PORTFOLIO_SHARE_PER_REGION,
                SERVICE_CATALOG_DESCRIBE_PORTFOLIO_SHARE_STATUS_PER_REGION,
            ]

    elif section_name == constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            resources = [
                SERVICE_CATALOG_SEARCH_PRODUCTS_AS_ADMIN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_PRODUCT_AS_ADMIN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DESCRIBE_PROVISIONING_ARTEFACT_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.DESCRIBE_PROVISIONING_PARAMETERS:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            resources = [
                SERVICE_CATALOG_DESCRIBE_PROVISIONING_PARAMETERS_PER_REGION_OF_ACCOUNT
            ]

    elif section_name == constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION:
        if status == "terminated":
            resources = [
                SERVICE_CATALOG_LIST_PORTFOLIOS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_LIST_PRINCIPALS_FOR_PORTFOLIO_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DISASSOCIATE_PRINCIPAL_FROM_PORTFOLIO_PER_REGION_OF_ACCOUNT,
            ]

        else:
            resources = [
                SERVICE_CATALOG_LIST_PORTFOLIOS_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_LIST_PRINCIPALS_FOR_PORTFOLIO_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_ASSOCIATE_PRINCIPAL_FROM_PORTFOLIO_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.APPS:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            resources = []

    elif section_name == constants.WORKSPACES:
        if status == "terminated":
            resources = []
        else:
            resources = []

    elif section_name == constants.WORKSPACE_ACCOUNT_PREPARATION:
        if status == "terminated":
            raise Exception("Not supported")
        else:
            resources = [
                CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
            ]

    elif (
        section_name == constants.PORTFOLIO_DISASSOCIATE_ALL_PRODUCTS_AND_THEIR_VERSIONS
    ):
        if status == "terminated":
            raise Exception("Not supported")
        else:
            resources = [
                SERVICE_CATALOG_SEARCH_PRODUCTS_AS_ADMIN_PER_REGION_OF_ACCOUNT,
                SERVICE_CATALOG_DISASSOCIATE_PRINCIPAL_FROM_PORTFOLIO_PER_REGION_OF_ACCOUNT,
            ]

    elif section_name == constants.RUN_DEPLOY_IN_SPOKE:
        resources = [CODEBUILD_START_BUILD_PER_REGION_OF_ACCOUNT]

    elif section_name == constants.GENERATE_MANIFEST:
        resources = [CAN_ONLY_BE_RUN_ONCE_AT_A_TIME]

    elif section_name == constants.GET_TEMPLATE_FROM_S3:
        resources = []  # DO NOT THROTTLE

    elif section_name == constants.GET_OR_CREATE_SERVICE_CONTROL_POLICIES_POLICY:
        resources = [
            ORGANIZATIONS_LIST_POLICIES_PER_REGION,
            ORGANIZATIONS_CREATE_POLICIES_PER_REGION,
            ORGANIZATIONS_DESCRIBE_POLICIES_PER_REGION,
            ORGANIZATIONS_UPDATE_POLICIES_PER_REGION,
        ]

    elif section_name == constants.GET_OR_CREATE_TAG_POLICIES_POLICY:
        resources = [
            ORGANIZATIONS_LIST_POLICIES_PER_REGION,
            ORGANIZATIONS_CREATE_POLICIES_PER_REGION,
            ORGANIZATIONS_DESCRIBE_POLICIES_PER_REGION,
            ORGANIZATIONS_UPDATE_POLICIES_PER_REGION,
        ]

    elif section_name == constants.PREPARE_ACCOUNT_FOR_STACKS:
        resources = [
            CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.CREATE_POLICIES:
        resources = [
            CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.ORGANIZATIONAL_UNITS:
        resources = [
            ORGANIZATIONS_CREATE_OU,
        ]

    elif section_name == constants.DESCRIBE_PORTFOLIO_SHARES:
        resources = [
            SERVICE_CATALOG_DESCRIBE_PORTFOLIO_SHARES_PER_REGION,
        ]

    elif section_name == constants.C7N_PREPARE_HUB_ACCOUNT_TASK:
        resources = [
            CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.C7N_FORWARD_EVENTS_FOR_ACCOUNT_TASK:
        resources = [
            CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.C7N_CREATE_CUSTODIAN_ROLE_TASK:
        resources = [
            CLOUDFORMATION_CREATE_OR_UPDATE_PER_REGION_OF_ACCOUNT,
        ]

    elif section_name == constants.C7N_AWS_LAMBDAS:
        resources = [
            # TODO choose what goes in here
        ]

    elif section_name == constants.C7N_FORWARD_EVENTS_FOR_REGION_TASK:
        resources = [
            # TODO choose what goes in here
        ]

    elif section_name == constants.C7N_DEPLOY_POLICIES_TASK:
        resources = [
            # TODO choose what goes in here
        ]

    result = list()
    for r in resources:
        try:
            result.append(r.format(**parameters_to_use))
        except KeyError as e:
            raise Exception(
                f"Failed to inject parameters into resource for '{section_name}': {r} was missing '{e}' in {parameters_to_use}"
            )
    return result
