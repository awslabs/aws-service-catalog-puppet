#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os

import pkg_resources

PREFIX = "SC-P--"
BOOTSTRAP_STACK_NAME = "servicecatalog-puppet"
PIPELINE_NAME = "servicecatalog-puppet-pipeline"
SERVICE_CATALOG_PUPPET_REPO_NAME = "ServiceCatalogPuppet"
OUTPUT = "output"
TEMPLATES = os.path.sep.join([OUTPUT, "templates"])
LAUNCHES_PATH = os.path.sep.join([OUTPUT, "launches"])
CONFIG_PARAM_NAME = "/servicecatalog-puppet/config"
CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN = "/servicecatalog-puppet/org-iam-role-arn"
CONFIG_PARAM_NAME_ORG_SCP_ROLE_ARN = "/servicecatalog-puppet/org-scp-role-arn"
PUPPET_ORG_ROLE_FOR_EXPANDS_ARN = "PuppetOrgRoleForExpandsArn"
HOME_REGION_PARAM_NAME = "/servicecatalog-puppet/home-region"

PROVISIONED = "provisioned"
TERMINATED = "terminated"

DEFAULT_TIMEOUT = 0
PARAMETERS = "parameters"
ACCOUNTS = "accounts"
MAPPINGS = "mappings"
LAUNCHES = "launches"
STACK = "stack"
STACKS = "stacks"
SPOKE_LOCAL_PORTFOLIOS = "spoke-local-portfolios"
LAMBDA_INVOCATIONS = "lambda-invocations"
ASSERTIONS = "assertions"
WORKSPACES = "workspaces"
CFCT = "cfct"
WORKSPACE = "workspace"
APPS = "apps"
APP = "app"
ASSERTION = "assertion"
CODE_BUILD_RUNS = "code-build-runs"
CODE_BUILD_RUN = "code-build-run"
SERVICE_CONTROL_POLICIES = "service-control-policies"
SERVICE_CONTROL_POLICY = "service-control-policy"
TAG_POLICIES = "tag-policies"
TAG_POLICY = "tag-policy"

ORGANIZATIONAL_UNIT = "organizational-unit"
ORGANIZATIONAL_UNITS = "organizational-units"

SIMULATE_POLICIES = "simulate-policies"
SIMULATE_POLICY = "simulate-policy"

ACTIONS = "actions"

LAUNCH = "launch"
LAMBDA_INVOCATION = "lambda-invocation"
SPOKE_LOCAL_PORTFOLIO = "spoke-local-portfolio"
ACTION = "action"

AFFINITY = "affinity"
AFFINITY_REGION = "region"
AFFINITY_ACCOUNT = "account"
AFFINITY_ACCOUNT_AND_REGION = "account-and-region"

RESULTS_DIRECTORY = "results"

NO_CHANGE = "NO_CHANGE"
CHANGE = "CHANGE"

EVENT_BUS_NAME = "servicecatalog-puppet-event-bus"
EVENT_BUS_IN_SPOKE_NAME = "servicecatalog-puppet-spoke-event-bus"
SERVICE_CATALOG_PUPPET_EVENT_SOURCE = "servicecatalog-puppet"
SERVICE_CATALOG_PUPPET_OPS_CENTER_SOURCE = "servicecatalog-puppet"

HOME_REGION = os.environ.get(
    "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")
)

EVENTBRIDGE_MAX_EVENTS_PER_CALL = 10

SPOKE_VERSION_SSM_PARAM_NAME = "service-catalog-puppet-spoke-version"
PUPPET_VERSION_SSM_PARAM_NAME = "service-catalog-puppet-version"
PUPPET_VERSION_INITIAL_SSM_PARAM_NAME = "service-catalog-puppet-version-initial"

SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED = "shared"
SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED = "terminated"

EXECUTION_MODE_ASYNC = "async"
EXECUTION_MODE_HUB = "hub"
EXECUTION_MODE_SPOKE = "spoke"
EXECUTION_MODE_HUB_AND_SPOKE_SPLIT = "hub-and-spoke-split"
EXECUTION_MODE_DEFAULT = EXECUTION_MODE_HUB
EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME = "servicecatalog-puppet-deploy-in-spoke"

SHARING_MODE_ACCOUNT = "ACCOUNT"
SHARING_MODE_AWS_ORGANIZATIONS = "AWS_ORGANIZATIONS"
SHARING_MODE_DEFAULT = SHARING_MODE_ACCOUNT

SHARE_TAG_OPTIONS_DEFAULT = False

PARTITION_DEFAULT = "aws"
PARTITION_ENVIRONMENTAL_VARIABLE_NAME = "PARTITION"
PARTITION_SSM_PARAMETER_VARIABLE_NAME = "/servicecatalog-puppet/partition"

PUPPET_ROLE_NAME_DEFAULT = "PuppetRole"
PUPPET_STACK_ROLE_NAME_DEFAULT = "PuppetStackRole"
PUPPET_ROLE_NAME_ENVIRONMENTAL_VARIABLE_NAME = "PUPPET_ROLE_NAME"
PUPPET_STACK_ROLE_NAME_ENVIRONMENTAL_VARIABLE_NAME = "PUPPET_STACK_ROLE_NAME"
PUPPET_ROLE_NAME_SSM_PARAMETER_VARIABLE_NAME = "/servicecatalog-puppet/puppet-role/name"

PUPPET_ROLE_PATH_DEFAULT = "/servicecatalog-puppet/"
PUPPET_ROLE_PATH_ENVIRONMENTAL_VARIABLE_NAME = "PUPPET_ROLE_PATH"
PUPPET_ROLE_PATH_SSM_PARAMETER_VARIABLE_NAME = "/servicecatalog-puppet/puppet-role/path"

DEPLOY_ENVIRONMENT_COMPUTE_TYPE_DEFAULT = "BUILD_GENERAL1_SMALL"

START_SHARED_SCHEDULER_COMMAND = "luigid --background --pidfile luigi.pid --logdir results/logs --state-path results/state"

CONFIG_REGIONS = "regions"
CONFIG_SHOULD_COLLECT_CLOUDFORMATION_EVENTS = "should_collect_cloudformation_events"
CONFIG_SHOULD_USE_STACKS_SERVICE_ROLE = "should_use_stacks_service_role"
MANIFEST_SHOULD_USE_STACKS_SERVICE_ROLE = "use_stacks_service_role"
CONFIG_SHOULD_USE_STACKS_SERVICE_ROLE_DEFAULT = False
CONFIG_SHOULD_USE_SHARED_SCHEDULER = "should_use_shared_scheduler"
CONFIG_SHOULD_EXPLODE_MANIFEST = "should_explode_manifest"

PUBLISHED_VERSION = pkg_resources.require("aws-service-catalog-puppet")[0].version
VERSION_OVERRIDE = "SCP_VERSION_OVERRIDE"
VERSION = os.getenv(VERSION_OVERRIDE, PUBLISHED_VERSION)

PRODUCT_GENERATION_METHOD_IMPORT = "import"
PRODUCT_GENERATION_METHOD_COPY = "copy"
PRODUCT_GENERATION_METHOD_DEFAULT = PRODUCT_GENERATION_METHOD_COPY

LUIGI_DEFAULT_LOG_LEVEL = "INFO"

ALL_SECTION_NAMES = [
    LAUNCHES,
    STACKS,
    SPOKE_LOCAL_PORTFOLIOS,
    LAMBDA_INVOCATIONS,
    CODE_BUILD_RUNS,
    ASSERTIONS,
    APPS,
    WORKSPACES,
    SERVICE_CONTROL_POLICIES,
    SIMULATE_POLICIES,
    TAG_POLICIES,
]
ALL_SECTION_NAMES_THAT_GENERATE_OUTPUTS = [
    LAUNCHES,
    STACKS,
    APPS,
    WORKSPACES,
]

ALL_SPOKE_EXECUTABLE_SECTION_NAMES = [
    LAUNCHES,
    STACKS,
    LAMBDA_INVOCATIONS,
    CODE_BUILD_RUNS,
    ASSERTIONS,
    APPS,
    WORKSPACES,
    SIMULATE_POLICIES,
]

ALL_SECTION_NAME_SINGULAR_AND_PLURAL_LIST = [
    (LAUNCH, LAUNCHES),
    (STACK, STACKS),
    (SPOKE_LOCAL_PORTFOLIO, SPOKE_LOCAL_PORTFOLIOS),
    (LAMBDA_INVOCATION, LAMBDA_INVOCATIONS),
    (CODE_BUILD_RUN, CODE_BUILD_RUNS),
    (ASSERTION, ASSERTIONS),
    (APP, APPS),
    (WORKSPACE, WORKSPACES),
    (SERVICE_CONTROL_POLICY, SERVICE_CONTROL_POLICIES),
    (SIMULATE_POLICY, SIMULATE_POLICIES),
    (TAG_POLICY, TAG_POLICIES),
    (ORGANIZATIONAL_UNIT, ORGANIZATIONAL_UNITS),
]

SECTION_NAME_SINGULAR_AND_PLURAL_LIST_THAT_SUPPORTS_PARAMETERS = [
    (LAUNCH, LAUNCHES),
    (STACK, STACKS),
    (LAMBDA_INVOCATION, LAMBDA_INVOCATIONS),
    (CODE_BUILD_RUN, CODE_BUILD_RUNS),
    (APP, APPS),
    (WORKSPACE, WORKSPACES),
]

SECTION_NAMES_THAT_SUPPORTS_PARAMETERS = [
    LAUNCHES,
    STACKS,
    LAMBDA_INVOCATIONS,
    CODE_BUILD_RUNS,
    APPS,
    WORKSPACES,
]

SECTION_SINGULAR_TO_PLURAL = {
    LAUNCH: LAUNCHES,
    STACK: STACKS,
    SPOKE_LOCAL_PORTFOLIO: SPOKE_LOCAL_PORTFOLIOS,
    LAMBDA_INVOCATION: LAMBDA_INVOCATIONS,
    CODE_BUILD_RUN: CODE_BUILD_RUNS,
    ASSERTION: ASSERTIONS,
    APP: APPS,
    WORKSPACE: WORKSPACES,
    SIMULATE_POLICY: SIMULATE_POLICIES,
    SERVICE_CONTROL_POLICY: SERVICE_CONTROL_POLICIES,
}

CODEBUILD_DEFAULT_IMAGE = "aws/codebuild/standard:4.0"

DEFAULT_TERRAFORM_VERSION_PARAMETER_NAME = (
    "/servicecatalog-puppet/terraform/default-version"
)
DEFAULT_TERRAFORM_VERSION_VALUE = "1.0.4"

EXECUTE_TERRAFORM_PROJECT_NAME = "servicecatalog-puppet-execute-terraform"
EXECUTE_DRY_RUN_TERRAFORM_PROJECT_NAME = (
    "servicecatalog-puppet-execute-dry-run-terraform"
)
TERMINATE_TERRAFORM_PROJECT_NAME = "servicecatalog-puppet-terminate-terraform"
TERMINATE_DRY_RUN_TERRAFORM_PROJECT_NAME = (
    "servicecatalog-puppet-terminate-dry-run-terraform"
)
TERRAFORM_SPOKE_PREP_STACK_NAME = f"{BOOTSTRAP_STACK_NAME}-terraform-execution"
STACK_SPOKE_PREP_STACK_NAME = f"{BOOTSTRAP_STACK_NAME}-stack-execution"

USE_SERVICE_ROLE_DEFAULT = False

MANIFEST_STATUS_FIELD_NAME = "status"
MANIFEST_STATUS_FIELD_VALUE_IGNORED = "ignored"

CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS = "should_delete_rollback_complete_stacks"
CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS_DEFAULT = False

PUPPET_LOGGER_NAME = "puppet-logger"
PUPPET_SCHEDULER_LOGGER_NAME = "puppet-logger-scheduler"

SPOKE_EXECUTION_MODE_DEPLOY_ENV_PARAMETER_NAME = (
    "/servicecatalog-puppet/spoke/deploy-environment-compute-type"
)
SPOKE_EXECUTION_MODE_DEPLOY_ENV_DEFAULT = "BUILD_GENERAL1_SMALL"

STATIC_HTML_PAGE = "static-html-page.html"

FULL_RUN_CODEBUILD_PROJECT_NAME = "servicecatalog-puppet-deploy"
SINGLE_ACCOUNT_RUN_CODEBUILD_PROJECT_NAME = "servicecatalog-puppet-single-account-run"

INITIALISER_STACK_NAME_SSM_PARAMETER = "service-catalog-puppet-initialiser-stack-name"

SECTIONS_THAT_SUPPORT_CONDITIONS = [
    LAUNCHES,
    SPOKE_LOCAL_PORTFOLIOS,
    STACKS,
    APPS,
    WORKSPACES,
    LAMBDA_INVOCATIONS,
    CODE_BUILD_RUNS,
    SERVICE_CONTROL_POLICIES,
    TAG_POLICIES,
    SIMULATE_POLICIES,
    ASSERTIONS,
]

SERVICE_CATALOG_PUPPET_MANIFEST_SSM_PREFIX = "/servicecatalog-puppet/manifest"

DEPLOY_TO_NAMES = {
    LAUNCHES: "deploy_to",
    STACKS: "deploy_to",
    SPOKE_LOCAL_PORTFOLIOS: "share_with",
    LAMBDA_INVOCATIONS: "invoke_for",
    CODE_BUILD_RUNS: "run_for",
    ASSERTIONS: "assert_for",
    APPS: "deploy_to",
    WORKSPACES: "deploy_to",
    SERVICE_CONTROL_POLICIES: "apply_to",
    SIMULATE_POLICIES: "simulate_for",
    TAG_POLICIES: "apply_to",
}

CLOUDFORMATION_HAPPY_STATUS = [
    "CREATE_COMPLETE",
    "UPDATE_ROLLBACK_COMPLETE",
    "UPDATE_COMPLETE",
    "IMPORT_COMPLETE",
    "IMPORT_ROLLBACK_COMPLETE",
]

CLOUDFORMATION_UNHAPPY_STATUS = [
    "CREATE_FAILED",
    "ROLLBACK_FAILED",
    "DELETE_FAILED",
    "UPDATE_FAILED",
    "UPDATE_ROLLBACK_FAILED",
    "IMPORT_ROLLBACK_FAILED",
]

CLOUDFORMATION_IN_PROGRESS_STATUS = [
    "CREATE_IN_PROGRESS",
    "ROLLBACK_IN_PROGRESS",
    "DELETE_IN_PROGRESS",
    "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
    "UPDATE_IN_PROGRESS",
    "UPDATE_ROLLBACK_IN_PROGRESS",
    "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS",
    "REVIEW_IN_PROGRESS",
    "IMPORT_IN_PROGRESS",
    "IMPORT_ROLLBACK_IN_PROGRESS",
]


SSM_OUTPUTS = "ssm_outputs"
SSM_PARAMETERS = "ssm_parameters"
BOTO3_PARAMETERS = "boto3_parameters"
SSM_PARAMETERS_WITH_A_PATH = "ssm_parameters_with_a_path"
PORTFOLIO_ASSOCIATIONS = "portfolio-associations"
PORTFOLIO_CONSTRAINTS_LAUNCH = "portfolio-constraints-launch"
PORTFOLIO_CONSTRAINTS_RESOURCE_UPDATE = "portfolio-constraints-resource_update"
PORTFOLIO_COPY = "portfolio-copy"
PORTFOLIO_IMPORT = "portfolio-import"
PORTFOLIO_SHARE_AND_ACCEPT_ACCOUNT = "portfolio-share-and-accept-account"
PORTFOLIO_SHARE_AND_ACCEPT_AWS_ORGANIZATIONS = (
    "portfolio-share-and-accept-aws_organizations"
)
PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS = (
    "portfolio-get-all-products-and-their-versions"
)
PORTFOLIO_DISASSOCIATE_ALL_PRODUCTS_AND_THEIR_VERSIONS = (
    "portfolio-disassociate-all-products-and-their-versions"
)
PORTFOLIO_LOCAL = "portfolio-local"
PORTFOLIO_IMPORTED = "portfolio-imported"
DESCRIBE_PROVISIONING_PARAMETERS = "describe-provisioning-parameters"
PORTFOLIO_PUPPET_ROLE_ASSOCIATION = "portfolio-puppet-role-association"
WORKSPACE_ACCOUNT_PREPARATION = "workspace-account-preparation"
RUN_DEPLOY_IN_SPOKE = "run-deploy-in-spoke"
GENERATE_MANIFEST = "generate-manifest"
GET_TEMPLATE_FROM_S3 = "get-template-from-s3"
GET_OR_CREATE_SERVICE_CONTROL_POLICIES_POLICY = (
    "get-or-create-service-control-policies-policy"
)
GET_OR_CREATE_TAG_POLICIES_POLICY = "get-or-create-tag-policies-policy"

PREPARE_ACCOUNT_FOR_STACKS = "prepare-account-for-stacks"
CREATE_POLICIES = "create-policies"


PARAMETERS_TO_TRY_AS_OPERATIONAL_DATA = [
    "puppet_account_id",
    "account_id",
    "region",
    "task_reference",
]


RUN_DEPLOY_IN_SPOKE_BUILDSPEC = """
      version: 0.2
      phases:
        install:
          runtime-versions:
            python: 3.9
          commands:
            - {}
        build:
          commands:
            - curl $TASK_REFERENCE_URL > manifest-task-reference.json
            - curl $MANIFEST_URL > manifest-expanded.yaml
            - servicecatalog-puppet --info deploy-in-spoke-from-task-reference --execution-mode spoke --puppet-account-id $PUPPET_ACCOUNT_ID --single-account $(aws sts get-caller-identity --query Account --output text) --home-region $HOME_REGION --regions $REGIONS --should-collect-cloudformation-events $SHOULD_COLLECT_CLOUDFORMATION_EVENTS --should-forward-events-to-eventbridge $SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE --should-forward-failures-to-opscenter $SHOULD_FORWARD_FAILURES_TO_OPSCENTER ${{PWD}}
      artifacts:
        files:
          - results/*/*
          - output/*/*
        name: DeployInSpokeProject
"""

SCHEDULER_THREADS_OR_PROCESSES_DEFAULT = "threads"


REPORTING_ROLE_NAME = "PuppetRoleForReporting"

SHARE_PRINCIPALS_DEFAULT = False

DESCRIBE_PORTFOLIO_SHARES = "describe-portfolio-shares"
