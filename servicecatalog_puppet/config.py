#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import functools
import logging
import os

import yaml
from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import constants

logger = logging.getLogger()


@functools.lru_cache(maxsize=32)
def get_config(puppet_account_id, default_region=None):
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f:
            conf = yaml.safe_load(f.read())
            return conf

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
def get_regions(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_REGIONS},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(constants.CONFIG_REGIONS)


@functools.lru_cache(maxsize=32)
def get_should_use_sns(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_SHOULD_COLLECT_CLOUDFORMATION_EVENTS},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(
        constants.CONFIG_SHOULD_COLLECT_CLOUDFORMATION_EVENTS, True
    )


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
def get_should_delete_rollback_complete_stacks(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(
        constants.CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS,
        constants.CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS_DEFAULT,
    )


@functools.lru_cache(maxsize=32)
def is_caching_enabled(puppet_account_id, default_region=None):
    logger.info(
        "getting is_caching_enabled,  default_region: {}".format(default_region)
    )
    if os.getenv(constants.CONFIG_IS_CACHING_ENABLED) is None:
        caching_enabled = get_config(puppet_account_id, default_region).get(
            "is_caching_enabled", False
        )
        os.putenv(constants.CONFIG_IS_CACHING_ENABLED, f"{caching_enabled}".lower())
    else:
        caching_enabled = (
            os.getenv(constants.CONFIG_IS_CACHING_ENABLED).lower() == "true"
        )
    return caching_enabled


@functools.lru_cache(maxsize=32)
def get_should_use_eventbridge(puppet_account_id, default_region=None):
    logger.info(
        "getting should_use_eventbridge,  default_region: {}".format(default_region)
    )
    return get_config(puppet_account_id, default_region).get(
        "should_forward_events_to_eventbridge", False
    )


@functools.lru_cache(maxsize=32)
def get_should_forward_failures_to_opscenter(puppet_account_id, default_region=None):
    logger.info(
        "getting should_forward_failures_to_opscenter,  default_region: {}".format(
            default_region
        )
    )
    return get_config(puppet_account_id, default_region).get(
        "should_forward_failures_to_opscenter", False
    )


@functools.lru_cache(maxsize=32)
def get_should_use_product_plans(puppet_account_id, default_region=None):
    logger.info(
        "getting should_use_product_plans,  default_region: {}".format(default_region)
    )
    return get_config(puppet_account_id, default_region).get(
        "should_use_product_plans", True
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


@functools.lru_cache(maxsize=32)
def get_global_sharing_mode_default(puppet_account_id, default_region=None):
    logger.info(
        "getting global_sharing_mode_default,  default_region: {}".format(
            default_region
        )
    )
    return get_config(puppet_account_id, default_region).get(
        "global_sharing_mode_default", constants.SHARING_MODE_DEFAULT
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
    return f"arn:{get_partition()}:iam::{puppet_account_id}:role{get_puppet_role_path()}{get_puppet_role_name()}"


@functools.lru_cache()
def get_puppet_stack_role_arn(puppet_account_id):
    logger.info("getting puppet_role_arn")
    return f"arn:{get_partition()}:iam::{puppet_account_id}:role{get_puppet_role_path()}{get_puppet_stack_role_name()}"


@functools.lru_cache(maxsize=32)
def get_local_config(what):
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f:
            conf = yaml.safe_load(f.read())
            return conf.get(what, None)
    else:
        return None


@functools.lru_cache()
def get_home_region(puppet_account_id):
    if get_local_config("home_region"):
        return get_local_config("home_region")
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


template_dir = asset_helpers.resolve_from_site_packages("templates")
env = Environment(loader=FileSystemLoader(template_dir), extensions=["jinja2.ext.do"],)


@functools.lru_cache(maxsize=32)
def get_puppet_account_id():
    with betterboto_client.ClientContextManager("sts") as sts:
        return sts.get_caller_identity().get("Account")


@functools.lru_cache(maxsize=32)
def get_current_account_id():
    with betterboto_client.ClientContextManager("sts") as sts:
        return sts.get_caller_identity().get("Account")


def get_ssm_config_for_parameter(account_ssm_param, required_parameter_name):
    if account_ssm_param.get("region") is not None:
        return {
            "name": account_ssm_param.get("name"),
            "region": account_ssm_param.get("region"),
            "parameter_name": required_parameter_name,
        }
    else:
        return {
            "name": account_ssm_param.get("name"),
            "parameter_name": required_parameter_name,
        }
