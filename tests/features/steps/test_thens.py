from behave import given, when, then, step

from servicecatalog_puppet import config, constants, sdk
from betterboto import client as betterboto_client


@then(u'the "{account_type}" account is bootstrapped with version "{version}" and "{role}" has an IAM Boundary')
def step_impl(context, account_type, version, role):
    param_name = ""

    if account_type == "spoke":
        param_name = constants.SPOKE_VERSION_SSM_PARAM_NAME
    elif account_type == "puppet":
        param_name = constants.PUPPET_VERSION_SSM_PARAM_NAME

    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.get_parameter(Name=param_name)


@then(u'the "{account_type}" account is bootstrapped with version "{version}"')
def step_impl(context, account_type, version):
    param_name = ""

    if account_type == "spoke":
        param_name = constants.SPOKE_VERSION_SSM_PARAM_NAME
    elif account_type == "puppet":
        param_name = constants.PUPPET_VERSION_SSM_PARAM_NAME

    with betterboto_client.ClientContextManager('ssm') as ssm:
        ssm.get_parameter(Name=param_name)
