#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
EXECUTION_MODE_DEFAULT = EXECUTION_MODE_HUB
EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME = "servicecatalog-puppet-deploy-in-spoke"

SHARING_MODE_ACCOUNT = "ACCOUNT"
SHARING_MODE_AWS_ORGANIZATIONS = "AWS_ORGANIZATIONS"
SHARING_MODE_DEFAULT = SHARING_MODE_ACCOUNT

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

CONFIG_IS_CACHING_ENABLED = "CONFIG_IS_CACHING_ENABLED"

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

PRODUCT_GENERATION_METHOD_DEFAULT = "copy"

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
]

ALL_SPOKE_EXECUTABLE_SECTION_NAMES = [
    LAUNCHES,
    STACKS,
    LAMBDA_INVOCATIONS,
    CODE_BUILD_RUNS,
    ASSERTIONS,
    APPS,
    WORKSPACES,
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


SPOKE_EXECUTION_MODE_DEPLOY_ENV_PARAMETER_NAME = (
    "/servicecatalog-puppet/spoke/deploy-environment-compute-type"
)
SPOKE_EXECUTION_MODE_DEPLOY_ENV_DEFAULT = "BUILD_GENERAL1_SMALL"

STATIC_HTML_PAGE = "static-html-page.html"

FULL_RUN_CODEBUILD_PROJECT_NAME = "servicecatalog-puppet-deploy"
SINGLE_ACCOUNT_RUN_CODEBUILD_PROJECT_NAME = "servicecatalog-puppet-single-account-run"

INITIALISER_STACK_NAME_SSM_PARAMETER = "service-catalog-puppet-initialiser-stack-name"


SERVICE_CONTROL_POLICIES = "service-control-policies"
