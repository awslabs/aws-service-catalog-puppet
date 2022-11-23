#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import functools
import json
from servicecatalog_puppet import serialisation_utils
import logging
import os

import yaml
from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import constants, environmental_variables

logger = logging.getLogger()


@functools.lru_cache(maxsize=32)
def get_config(puppet_account_id, default_region=None):
    logger.info("getting config,  default_region: {}".format(default_region))
    region = default_region if default_region else get_home_region(puppet_account_id)
    with betterboto_client.CrossAccountClientContextManager(
        "ssm",
        get_puppet_role_arn(puppet_account_id),
        f"{puppet_account_id}-{region}-{get_puppet_role_name()}",
        region_name=region,
    ) as ssm:
        response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
        return yaml.safe_load(response.get("Parameter").get("Value"))


@functools.lru_cache(maxsize=32)
def get_should_use_stacks_service_role(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_SHOULD_USE_STACKS_SERVICE_ROLE},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(
        constants.CONFIG_SHOULD_USE_STACKS_SERVICE_ROLE,
        constants.CONFIG_SHOULD_USE_STACKS_SERVICE_ROLE_DEFAULT,
    )


@functools.lru_cache(maxsize=32)
def get_should_use_shared_scheduler(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_SHOULD_USE_SHARED_SCHEDULER},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(
        constants.CONFIG_SHOULD_USE_SHARED_SCHEDULER, False
    )


@functools.lru_cache(maxsize=32)
def get_should_explode_manifest(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_SHOULD_EXPLODE_MANIFEST},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(
        constants.CONFIG_SHOULD_EXPLODE_MANIFEST, False
    )


@functools.lru_cache()
def get_partition():
    logger.info(f"getting partition")
    return os.getenv(
        constants.PARTITION_ENVIRONMENTAL_VARIABLE_NAME, constants.PARTITION_DEFAULT
    )


@functools.lru_cache()
def get_puppet_role_name():
    logger.info("getting puppet_role_name")
    return os.getenv(
        constants.PUPPET_ROLE_NAME_ENVIRONMENTAL_VARIABLE_NAME,
        constants.PUPPET_ROLE_NAME_DEFAULT,
    )


@functools.lru_cache()
def get_puppet_stack_role_name():
    logger.info("getting puppet_stack_role_name")
    return os.getenv(
        constants.PUPPET_STACK_ROLE_NAME_ENVIRONMENTAL_VARIABLE_NAME,
        constants.PUPPET_STACK_ROLE_NAME_DEFAULT,
    )


@functools.lru_cache()
def get_puppet_role_path():
    logger.info("getting puppet_role_path")
    return os.getenv(
        constants.PUPPET_ROLE_PATH_ENVIRONMENTAL_VARIABLE_NAME,
        constants.PUPPET_ROLE_PATH_DEFAULT,
    )


@functools.lru_cache()
def get_puppet_role_arn(puppet_account_id):
    logger.info("getting puppet_role_arn")
    return get_role_arn(puppet_account_id, get_puppet_role_name())


@functools.lru_cache()
def get_role_arn(puppet_account_id, role_name):
    logger.info("getting puppet_role_arn")
    return f"arn:{get_partition()}:iam::{puppet_account_id}:role{get_puppet_role_path()}{role_name}"


@functools.lru_cache()
def get_puppet_stack_role_arn(puppet_account_id):
    logger.info("getting puppet_role_arn")
    return f"arn:{get_partition()}:iam::{puppet_account_id}:role{get_puppet_role_path()}{get_puppet_stack_role_name()}"


@functools.lru_cache()
def get_home_region(puppet_account_id):
    if os.environ.get(environmental_variables.HOME_REGION):
        return os.environ.get(environmental_variables.HOME_REGION)
    with betterboto_client.CrossAccountClientContextManager(
        "ssm",
        get_puppet_role_arn(puppet_account_id),
        f"{puppet_account_id}-{get_puppet_role_name()}",
    ) as ssm:
        response = ssm.get_parameter(Name=constants.HOME_REGION_PARAM_NAME)
        return response.get("Parameter").get("Value")


@functools.lru_cache(maxsize=32)
def get_org_iam_role_arn(puppet_account_id):
    with betterboto_client.CrossAccountClientContextManager(
        "ssm",
        get_puppet_role_arn(puppet_account_id),
        f"{puppet_account_id}-{get_puppet_role_name()}",
        region_name=get_home_region(puppet_account_id),
    ) as ssm:
        try:
            response = ssm.get_parameter(
                Name=constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN
            )
            return response.get("Parameter").get("Value")
        except ssm.exceptions.ParameterNotFound:
            logger.info("No org role set")
            return None


@functools.lru_cache(maxsize=32)
def get_org_scp_role_arn(puppet_account_id):
    with betterboto_client.CrossAccountClientContextManager(
        "ssm",
        get_puppet_role_arn(puppet_account_id),
        f"{puppet_account_id}-{get_puppet_role_name()}",
        region_name=get_home_region(puppet_account_id),
    ) as ssm:
        try:
            response = ssm.get_parameter(
                Name=constants.CONFIG_PARAM_NAME_ORG_SCP_ROLE_ARN
            )
            return response.get("Parameter").get("Value")
        except ssm.exceptions.ParameterNotFound:
            logger.info("No org role set")
            return None


template_dir = asset_helpers.resolve_from_site_packages("templates")
env = Environment(loader=FileSystemLoader(template_dir), extensions=["jinja2.ext.do"],)


def get_num_workers():
    return int(os.environ.get(environmental_variables.NUM_WORKERS))


def get_puppet_account_id():
    return os.environ.get(environmental_variables.PUPPET_ACCOUNT_ID)


def get_single_account_id():
    return os.environ.get(environmental_variables.SINGLE_ACCOUNT_ID)


def get_executor_account_id():
    return os.environ.get(environmental_variables.EXECUTOR_ACCOUNT_ID)


def get_execution_mode():
    return os.environ.get(environmental_variables.EXECUTION_MODE)


def get_should_use_eventbridge():
    return (
        os.environ.get(
            environmental_variables.SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE, "FALSE"
        ).upper()
        == "TRUE"
    )


def get_should_forward_failures_to_opscenter():
    return (
        os.environ.get(
            environmental_variables.SHOULD_FORWARD_FAILURES_TO_OPSCENTER, "FALSE"
        ).upper()
        == "TRUE"
    )


def get_regions():
    return serialisation_utils.json_loads(
        os.environ.get(environmental_variables.REGIONS)
    )


def get_output_cache_starting_point():
    return os.environ.get(environmental_variables.OUTPUT_CACHE_STARTING_POINT)


def is_caching_enabled():
    return os.environ.get(environmental_variables.IS_CACHING_ENABLED).lower() == "true"


def get_initialiser_stack_tags():
    return os.environ.get(environmental_variables.INITIALISER_STACK_TAGS)


def get_global_sharing_mode_default():
    return os.environ.get(environmental_variables.GLOBAL_SHARING_MODE)


def get_global_share_tag_options_default():
    return os.environ.get(environmental_variables.GLOBAL_SHARE_TAG_OPTIONS)


def get_global_share_principals_default():
    return os.environ.get(environmental_variables.GLOBAL_SHARE_PRINCIPALS)


def get_on_complete_url():
    return os.environ.get(environmental_variables.ON_COMPLETE_URL, "")


def get_should_delete_rollback_complete_stacks():
    return os.environ.get(
        environmental_variables.SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS
    )


def get_should_use_product_plans():
    return os.environ.get(environmental_variables.SHOULD_USE_PRODUCT_PLANS)


def get_spoke_execution_mode_deploy_env():
    return os.environ.get(environmental_variables.SPOKE_EXECUTION_MODE_DEPLOY_ENV)


def get_should_use_sns():
    return (
        os.environ.get(environmental_variables.SHOULD_USE_SNS, "FALSE").upper()
        == "TRUE"
    )


def get_scheduler_threads_or_processes():
    return os.environ.get(
        environmental_variables.SCHEDULER_THREADS_OR_PROCESSES,
        constants.SCHEDULER_THREADS_OR_PROCESSES_DEFAULT,
    )


def get_reporting_role_arn(puppet_account_id):
    return get_role_arn(puppet_account_id, constants.REPORTING_ROLE_NAME)
