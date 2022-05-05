#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0


def test_constants_values():
    # setup
    from servicecatalog_puppet import constants

    # exercise
    # verify
    assert constants.PREFIX == "SC-P--"
    assert constants.BOOTSTRAP_STACK_NAME == "servicecatalog-puppet"
    assert constants.PIPELINE_NAME == "servicecatalog-puppet-pipeline"
    assert constants.SERVICE_CATALOG_PUPPET_REPO_NAME == "ServiceCatalogPuppet"
    assert constants.OUTPUT == "output"

    assert constants.CONFIG_PARAM_NAME == "/servicecatalog-puppet/config"
    assert (
        constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN
        == "/servicecatalog-puppet/org-iam-role-arn"
    )
    assert constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN == "PuppetOrgRoleForExpandsArn"
    assert constants.HOME_REGION_PARAM_NAME == "/servicecatalog-puppet/home-region"

    assert constants.PROVISIONED == "provisioned"
    assert constants.TERMINATED == "terminated"

    assert constants.DEFAULT_TIMEOUT == 0
    assert constants.PARAMETERS == "parameters"
    assert constants.ACCOUNTS == "accounts"
    assert constants.MAPPINGS == "mappings"
    assert constants.LAUNCHES == "launches"
    assert constants.STACKS == "stacks"
    assert constants.SPOKE_LOCAL_PORTFOLIOS == "spoke-local-portfolios"
    assert constants.LAMBDA_INVOCATIONS == "lambda-invocations"
    assert constants.ASSERTIONS == "assertions"
    assert constants.ASSERTION == "assertion"
    assert constants.CODE_BUILD_RUNS == "code-build-runs"
    assert constants.CODE_BUILD_RUN == "code-build-run"
    assert constants.ACTIONS == "actions"

    assert constants.LAUNCH == "launch"
    assert constants.STACK == "stack"
    assert constants.LAMBDA_INVOCATION == "lambda-invocation"
    assert constants.SPOKE_LOCAL_PORTFOLIO == "spoke-local-portfolio"
    assert constants.ACTION == "action"

    assert constants.AFFINITY == "affinity"
    assert constants.AFFINITY_REGION == "region"
    assert constants.AFFINITY_ACCOUNT == "account"
    assert constants.AFFINITY_ACCOUNT_AND_REGION == "account-and-region"

    assert constants.ALL_SECTION_NAMES == [
        constants.LAUNCHES,
        constants.STACKS,
        constants.SPOKE_LOCAL_PORTFOLIOS,
        constants.LAMBDA_INVOCATIONS,
        constants.CODE_BUILD_RUNS,
        constants.ASSERTIONS,
        constants.APPS,
        constants.WORKSPACES,
        constants.SERVICE_CONTROL_POLICIES,
        constants.SIMULATE_POLICIES,
        constants.TAG_POLICIES,
    ]
    assert constants.RESULTS_DIRECTORY == "results"
    assert constants.NO_CHANGE == "NO_CHANGE"
    assert constants.CHANGE == "CHANGE"
    assert constants.EVENT_BUS_NAME == "servicecatalog-puppet-event-bus"
    assert constants.EVENT_BUS_IN_SPOKE_NAME == "servicecatalog-puppet-spoke-event-bus"
    assert constants.SERVICE_CATALOG_PUPPET_EVENT_SOURCE == "servicecatalog-puppet"
    assert constants.SERVICE_CATALOG_PUPPET_OPS_CENTER_SOURCE == "servicecatalog-puppet"

    assert constants.EVENTBRIDGE_MAX_EVENTS_PER_CALL == 10
    assert (
        constants.SPOKE_VERSION_SSM_PARAM_NAME == "service-catalog-puppet-spoke-version"
    )
    assert constants.PUPPET_VERSION_SSM_PARAM_NAME == "service-catalog-puppet-version"
    assert (
        constants.PUPPET_VERSION_INITIAL_SSM_PARAM_NAME
        == "service-catalog-puppet-version-initial"
    )
    assert constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED == "shared"
    assert constants.SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED == "terminated"
    assert constants.EXECUTION_MODE_ASYNC == "async"
    assert constants.EXECUTION_MODE_HUB == "hub"
    assert constants.EXECUTION_MODE_SPOKE == "spoke"
    assert constants.EXECUTION_MODE_DEFAULT == constants.EXECUTION_MODE_HUB
    assert (
        constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME
        == "servicecatalog-puppet-deploy-in-spoke"
    )
    assert constants.SHARING_MODE_ACCOUNT == "ACCOUNT"
    assert constants.SHARING_MODE_AWS_ORGANIZATIONS == "AWS_ORGANIZATIONS"
    assert constants.SHARING_MODE_DEFAULT == constants.SHARING_MODE_ACCOUNT
    assert constants.PARTITION_DEFAULT == "aws"
    assert constants.PARTITION_ENVIRONMENTAL_VARIABLE_NAME == "PARTITION"
    assert (
        constants.PARTITION_SSM_PARAMETER_VARIABLE_NAME
        == "/servicecatalog-puppet/partition"
    )
    assert constants.PUPPET_ROLE_NAME_DEFAULT == "PuppetRole"
    assert constants.PUPPET_ROLE_NAME_ENVIRONMENTAL_VARIABLE_NAME == "PUPPET_ROLE_NAME"
    assert (
        constants.PUPPET_ROLE_NAME_SSM_PARAMETER_VARIABLE_NAME
        == "/servicecatalog-puppet/puppet-role/name"
    )
    assert constants.PUPPET_ROLE_PATH_DEFAULT == "/servicecatalog-puppet/"
    assert constants.PUPPET_ROLE_PATH_ENVIRONMENTAL_VARIABLE_NAME == "PUPPET_ROLE_PATH"
    assert (
        constants.PUPPET_ROLE_PATH_SSM_PARAMETER_VARIABLE_NAME
        == "/servicecatalog-puppet/puppet-role/path"
    )
    assert constants.DEPLOY_ENVIRONMENT_COMPUTE_TYPE_DEFAULT == "BUILD_GENERAL1_SMALL"
    assert constants.CONFIG_IS_CACHING_ENABLED == "CONFIG_IS_CACHING_ENABLED"
    assert (
        constants.START_SHARED_SCHEDULER_COMMAND
        == "luigid --background --pidfile luigi.pid --logdir results/logs --state-path results/state"
    )
    assert constants.CONFIG_REGIONS == "regions"
    assert (
        constants.CONFIG_SHOULD_COLLECT_CLOUDFORMATION_EVENTS
        == "should_collect_cloudformation_events"
    )
    assert constants.CONFIG_SHOULD_USE_SHARED_SCHEDULER == "should_use_shared_scheduler"
    assert constants.CONFIG_SHOULD_EXPLODE_MANIFEST == "should_explode_manifest"

    assert constants.VERSION_OVERRIDE == "SCP_VERSION_OVERRIDE"

    assert constants.PRODUCT_GENERATION_METHOD_DEFAULT == "copy"
    assert constants.LUIGI_DEFAULT_LOG_LEVEL == "INFO"
    assert constants.ALL_SECTION_NAME_SINGULAR_AND_PLURAL_LIST == [
        (constants.LAUNCH, constants.LAUNCHES),
        (constants.STACK, constants.STACKS),
        (constants.SPOKE_LOCAL_PORTFOLIO, constants.SPOKE_LOCAL_PORTFOLIOS),
        (constants.LAMBDA_INVOCATION, constants.LAMBDA_INVOCATIONS),
        (constants.CODE_BUILD_RUN, constants.CODE_BUILD_RUNS),
        (constants.ASSERTION, constants.ASSERTIONS),
        (constants.APP, constants.APPS),
        (constants.WORKSPACE, constants.WORKSPACES),
    ]
    assert constants.SECTION_NAME_SINGULAR_AND_PLURAL_LIST_THAT_SUPPORTS_PARAMETERS == [
        (constants.LAUNCH, constants.LAUNCHES),
        (constants.STACK, constants.STACKS),
        (constants.LAMBDA_INVOCATION, constants.LAMBDA_INVOCATIONS),
        (constants.CODE_BUILD_RUN, constants.CODE_BUILD_RUNS),
        (constants.APP, constants.APPS),
        (constants.WORKSPACE, constants.WORKSPACES),
    ]
    assert constants.SECTION_SINGULAR_TO_PLURAL == {
        constants.LAUNCH: constants.LAUNCHES,
        constants.STACK: constants.STACKS,
        constants.SPOKE_LOCAL_PORTFOLIO: constants.SPOKE_LOCAL_PORTFOLIOS,
        constants.LAMBDA_INVOCATION: constants.LAMBDA_INVOCATIONS,
        constants.CODE_BUILD_RUN: constants.CODE_BUILD_RUNS,
        constants.ASSERTION: constants.ASSERTIONS,
        constants.APP: constants.APPS,
        constants.WORKSPACE: constants.WORKSPACES,
        constants.SIMULATE_POLICY: constants.SIMULATE_POLICIES,
        constants.SERVICE_CONTROL_POLICY: constants.SERVICE_CONTROL_POLICIES,
    }
