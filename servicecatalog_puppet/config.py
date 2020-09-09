import functools
import os

import pkg_resources
import yaml
from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import constants

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
        f"arn:aws:iam::{puppet_account_id}:role/servicecatalog-puppet/PuppetRole",
        f"{puppet_account_id}-{region}-PuppetRole",
        region_name=region,
    ) as ssm:
        response = ssm.get_parameter(Name=constants.CONFIG_PARAM_NAME)
        return yaml.safe_load(response.get("Parameter").get("Value"))


@functools.lru_cache(maxsize=32)
def get_regions(puppet_account_id, default_region=None):
    logger.info("getting regions,  default_region: {}".format(default_region))
    return get_config(puppet_account_id, default_region).get("regions")


@functools.lru_cache(maxsize=32)
def get_should_use_sns(puppet_account_id, default_region=None):
    logger.info("getting should_use_sns,  default_region: {}".format(default_region))
    return get_config(puppet_account_id, default_region).get(
        "should_collect_cloudformation_events", True
    )


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
        f"arn:aws:iam::{puppet_account_id}:role/servicecatalog-puppet/PuppetRole",
        f"{puppet_account_id}-PuppetRole",
    ) as ssm:
        response = ssm.get_parameter(Name=constants.HOME_REGION_PARAM_NAME)
        return response.get("Parameter").get("Value")


@functools.lru_cache(maxsize=32)
def get_org_iam_role_arn(puppet_account_id):
    with betterboto_client.CrossAccountClientContextManager(
        "ssm",
        f"arn:aws:iam::{puppet_account_id}:role/servicecatalog-puppet/PuppetRole",
        f"{puppet_account_id}-PuppetRole",
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


# TODO - not used?
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


def get_puppet_version():
    return pkg_resources.get_distribution("aws-service-catalog-puppet").version
