from behave import given, when, then, step

from servicecatalog_puppet import config, constants, sdk
from betterboto import client as betterboto_client


@given(u'a "{account_type}" account has not been bootstrapped')
def step_impl(context, account_type):
    if account_type == "puppet":
        sdk.uninstall()
    elif account_type == "spoke":
        sdk.release_spoke()


@given(u'a "{account_type}" account has been bootstrapped with version "{version}"')
def step_impl(context, account_type, version):
    with betterboto_client.ClientContextManager('cloudformation') as cloudformation:
        if account_type == "puppet":
            stacks = cloudformation.describe_stacks_single_page(
                StackName=constants.BOOTSTRAP_STACK_NAME
            ).get('Stacks', [])
        elif account_type == "spoke":
            stacks = cloudformation.describe_stacks_single_page(
                StackName=f"{constants.BOOTSTRAP_STACK_NAME}-spoke"
            ).get('Stacks', [])

        completed = False
        for stack in stacks:
            if stack.get('StackStatus') == 'CREATE_COMPLETE':
                completed = True
                break

        if not completed:
            raise Exception("not bootstrapped correctly or at all")


@given(u'the config has been set')
def step_impl(context):
    sdk.upload_config({
        "regions": [
            'eu-west-1',
            'eu-west-2',
        ],
        "should_collect_cloudformation_events": False,
        "should_forward_events_to_eventbridge": False,
        "should_forward_failures_to_opscenter": False,
    })
