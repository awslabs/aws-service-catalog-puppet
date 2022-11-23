#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import functools
import logging

import yaml
from betterboto import client as betterboto_client

from servicecatalog_puppet import constants, config

logger = logging.getLogger()


@functools.lru_cache(maxsize=32)
def get_config(puppet_account_id, default_region=None):
    logger.info("getting config,  default_region: {}".format(default_region))
    region = (
        default_region if default_region else config.get_home_region(puppet_account_id)
    )
    with betterboto_client.CrossAccountClientContextManager(
        "ssm",
        config.get_puppet_role_arn(puppet_account_id),
        f"{puppet_account_id}-{region}-{config.get_puppet_role_name()}",
        region_name=region,
    ) as ssm:
        response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
        return yaml.safe_load(response.get("Parameter").get("Value"))


@functools.lru_cache(maxsize=32)
def get_should_use_sns(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_SHOULD_COLLECT_CLOUDFORMATION_EVENTS},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(
        constants.CONFIG_SHOULD_COLLECT_CLOUDFORMATION_EVENTS, True
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
def get_should_use_product_plans(puppet_account_id, default_region=None):
    logger.info(
        "getting should_use_product_plans,  default_region: {}".format(default_region)
    )
    return get_config(puppet_account_id, default_region).get(
        "should_use_product_plans", True
    )


@functools.lru_cache(maxsize=32)
def get_initialiser_stack_tags():
    with betterboto_client.ClientContextManager("ssm") as ssm:
        try:
            response = ssm.get_parameter(
                Name=constants.INITIALISER_STACK_NAME_SSM_PARAMETER
            )
            initialiser_stack_name = response.get("Parameter").get("Value")
            with betterboto_client.ClientContextManager(
                "cloudformation"
            ) as cloudformation:
                paginator = cloudformation.get_paginator("describe_stacks")
                for page in paginator.paginate(StackName=initialiser_stack_name,):
                    for stack in page.get("Stacks", []):
                        if stack.get("StackStatus") in [
                            "CREATE_IN_PROGRESS",
                            "CREATE_COMPLETE",
                            "UPDATE_IN_PROGRESS",
                            "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
                            "UPDATE_COMPLETE",
                        ]:
                            return stack.get("Tags")
                        else:
                            raise Exception(
                                f"Initialiser stack: {initialiser_stack_name} in state: {stack.get('StackStatus')}"
                            )
        except ssm.exceptions.ParameterNotFound:
            logger.warning(
                f"Could not find SSM parameter: {constants.INITIALISER_STACK_NAME_SSM_PARAMETER}, do not know the tags to use"
            )
            return []


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
def get_regions(puppet_account_id, default_region=None):
    logger.info(
        f"getting {constants.CONFIG_REGIONS},  default_region: {default_region}"
    )
    return get_config(puppet_account_id, default_region).get(constants.CONFIG_REGIONS)


@functools.lru_cache(maxsize=32)
def get_puppet_account_id():
    with betterboto_client.ClientContextManager("sts") as sts:
        return sts.get_caller_identity().get("Account")


@functools.lru_cache(maxsize=32)
def get_current_account_id():
    with betterboto_client.ClientContextManager("sts") as sts:
        return sts.get_caller_identity().get("Account")


@functools.lru_cache(maxsize=32)
def is_caching_enabled(puppet_account_id, default_region=None):
    return get_config(puppet_account_id, default_region).get(
        "is_caching_enabled", False
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


@functools.lru_cache(maxsize=32)
def get_global_share_tag_options_default(puppet_account_id, default_region=None):
    logger.info(
        "getting global_share_tag_options_default,  default_region: {}".format(
            default_region
        )
    )
    return get_config(puppet_account_id, default_region).get(
        "global_share_tag_options_default", constants.SHARE_TAG_OPTIONS_DEFAULT
    )


@functools.lru_cache(maxsize=32)
def get_global_share_principals_default(puppet_account_id, default_region=None):
    logger.info(
        "getting global_share_principals_default,  default_region: {}".format(
            default_region
        )
    )
    return get_config(puppet_account_id, default_region).get(
        "global_share_principals_default", constants.SHARE_PRINCIPALS_DEFAULT
    )


def get_spoke_deploy_environment_compute_type(puppet_account_id, default_region):
    logger.info(
        "getting spoke_deploy_environment_compute_type,  default_region: {}".format(
            default_region
        )
    )
    return get_config(puppet_account_id, default_region).get(
        "spoke_deploy_environment_compute_type",
        constants.SPOKE_EXECUTION_MODE_DEPLOY_ENV_DEFAULT,
    )


def get_scheduler_threads_or_processes(puppet_account_id, default_region):
    logger.info(
        "getting scheduler_threads_or_processes,  default_region: {}".format(
            default_region
        )
    )
    return get_config(puppet_account_id, default_region).get(
        "scheduler_threads_or_processes",
        constants.SCHEDULER_THREADS_OR_PROCESSES_DEFAULT,
    )
