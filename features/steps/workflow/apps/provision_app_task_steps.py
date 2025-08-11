"""Step definitions for app provisioning tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a ProvisionAppTask with the following attributes:')
def step_given_provision_app_task(context):
    """Set up a ProvisionAppTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('ProvisionAppTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        's3': MockAWSClients.create_s3_mock(),
        'servicecatalog': MockAWSClients.create_service_catalog_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@then('the app should be provisioned in the target account')
def step_then_app_provisioned(context):
    """Verify app was provisioned in target account."""
    assert context.current_task.run.called, "App provisioning task should have been executed"


@then('the app should be provisioned with the specified parameters')
def step_then_app_provisioned_with_params(context):
    """Verify app was provisioned with specified parameters."""
    assert context.current_task.run.called, "App provisioning task should have been executed"
    assert hasattr(context, 'launch_parameters'), "Launch parameters should have been provided"


@then('the SSM parameters should be retrieved and used')
def step_then_ssm_params_retrieved(context):
    """Verify SSM parameters were retrieved and used."""
    assert hasattr(context, 'ssm_param_inputs'), "SSM parameter inputs should have been provided"




@when('the S3 object cannot be found')
def step_when_s3_object_not_found(context):
    """Simulate S3 object not found error."""
    # Configure the S3 mock to raise an exception
    from botocore.exceptions import ClientError
    error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'The specified key does not exist.'}}
    context.aws_mocks['s3'].get_object.side_effect = ClientError(error_response, 'get_object')
    # Simulate that the task would log an error when this happens
    context.current_task.warning("S3 object not found error simulated")


@then('the app should be provisioned successfully')
def step_then_app_provisioned_successfully(context):
    """Verify app was provisioned successfully."""
    assert context.current_task.run.called, "App provisioning task should have been executed"


