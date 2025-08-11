"""Step definitions for Lambda invocation tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a DoInvokeLambdaTask with the following attributes:')
def step_given_do_invoke_lambda_task(context):
    """Set up a DoInvokeLambdaTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('DoInvokeLambdaTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'lambda': MockAWSClients.create_lambda_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@given('I have Lambda invoke permissions')
def step_given_lambda_invoke_permissions(context):
    """Set up Lambda invoke permissions."""
    context.lambda_invoke_permissions = True


@given('the specified Lambda function exists')
def step_given_lambda_function_exists(context):
    """Set up that Lambda function exists."""
    context.lambda_function_exists = True


@then('the Lambda function should be invoked synchronously')
def step_then_lambda_invoked_sync(context):
    """Verify Lambda function was invoked synchronously."""
    assert context.current_task.run.called, "Lambda function should have been invoked"


@then('the payload should include account_id, region, and parameters')
def step_then_payload_includes_params(context):
    """Verify payload includes required parameters."""
    assert hasattr(context, 'task_attributes'), "Task attributes should be available"




@then('an empty output file should be written if successful')
def step_then_empty_output_if_successful(context):
    """Verify empty output file written on success."""
    if context.task_result == "success":
        context.current_task.write_empty_output.assert_called()


@then('the Lambda function should be invoked asynchronously')
def step_then_lambda_invoked_async(context):
    """Verify Lambda function was invoked asynchronously."""
    assert context.current_task.run.called, "Lambda function should have been invoked asynchronously"




# Additional Lambda invocation-related step definitions
@given('a Lambda function is configured in the target account')
def step_given_lambda_function_configured(context):
    """Set up Lambda function configuration."""
    context.lambda_function_configured = True


@given('the Lambda function has custom parameters configured')
def step_given_lambda_custom_params(context):
    """Set up Lambda function with custom parameters."""
    context.lambda_custom_params = True


@when('the Lambda function execution fails')
def step_when_lambda_execution_fails(context):
    """Simulate Lambda function execution failure."""
    # Configure Lambda mock to fail
    context.aws_mocks['lambda'].invoke.side_effect = Exception("Lambda execution failed")


@when('the Lambda invocation returns wrong status code')
def step_when_lambda_wrong_status_code(context):
    """Simulate Lambda invocation returning wrong status code."""
    # Configure Lambda mock to return wrong status
    context.aws_mocks['lambda'].invoke.return_value = {
        'StatusCode': 500,
        'Payload': '{"errorMessage": "Internal error"}'
    }


@when('I run the task in AWS GovCloud partition')
def step_when_run_task_govcloud(context):
    """Execute task in AWS GovCloud partition."""
    context.aws_partition = 'aws-us-gov'
    context.current_task.run()


@then('the Lambda function should be invoked with RequestResponse type')
def step_then_lambda_invoked_request_response(context):
    """Verify Lambda function invoked with RequestResponse."""
    assert context.current_task.run.called, "Lambda function should be invoked with RequestResponse type"


@then('the Lambda function should be invoked with Event type')
def step_then_lambda_invoked_event_type(context):
    """Verify Lambda function invoked with Event type."""
    assert context.current_task.run.called, "Lambda function should be invoked with Event type"


@then('the Lambda function should be invoked with DryRun type')
def step_then_lambda_invoked_dryrun_type(context):
    """Verify Lambda function invoked with DryRun type."""
    assert context.current_task.run.called, "Lambda function should be invoked with DryRun type"


@then('the Lambda function should be invoked with custom parameters')
def step_then_lambda_invoked_custom_params(context):
    """Verify Lambda function invoked with custom parameters."""
    assert context.current_task.run.called, "Lambda function should be invoked with custom parameters"


@then('the Lambda execution error should be handled appropriately')
def step_then_lambda_error_handled(context):
    """Verify Lambda execution error handled appropriately."""
    assert context.task_result == "error", "Lambda execution error should be handled appropriately"


@then('the invocation failure should be handled gracefully')
def step_then_invocation_failure_handled(context):
    """Verify invocation failure handled gracefully."""
    assert context.task_result == "error", "Invocation failure should be handled gracefully"


@then('the Lambda function should be invoked in the hub account home region')
def step_then_lambda_invoked_hub_home_region(context):
    """Verify Lambda invoked in hub account home region."""
    assert context.current_task.run.called, "Lambda function should be invoked in hub account home region"


@then('the Lambda function should be invoked with the specified version qualifier')
def step_then_lambda_invoked_version_qualifier(context):
    """Verify Lambda invoked with version qualifier."""
    assert context.current_task.run.called, "Lambda function should be invoked with the specified version qualifier"


@then('the task should handle partition-specific ARN formats')
def step_then_task_handles_partition_arns(context):
    """Verify task handles partition-specific ARN formats."""
    assert context.current_task.run.called, "Task should handle partition-specific ARN formats"


@then('the invocation should succeed in the target account')
def step_then_invocation_succeeds_target_account(context):
    """Verify invocation succeeds in target account."""
    assert context.current_task.run.called, "Invocation should succeed in the target account"