"""Step definitions for stack provisioning tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a ProvisionStackTask with the following attributes:')
def step_given_provision_stack_task(context):
    """Set up a ProvisionStackTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('ProvisionStackTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'cloudformation': MockAWSClients.create_cloudformation_mock(),
        's3': MockAWSClients.create_s3_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes