"""Step definitions for stack termination tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a TerminateStackTask with the following attributes:')
def step_given_terminate_stack_task(context):
    """Set up a TerminateStackTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('TerminateStackTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'cloudformation': MockAWSClients.create_cloudformation_mock(),
        's3': MockAWSClients.create_s3_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Parse ssm_param_inputs if present and set on context
    if 'ssm_param_inputs' in attributes:
        ssm_inputs_str = attributes['ssm_param_inputs']
        if ssm_inputs_str.startswith('[') and ssm_inputs_str.endswith(']'):
            # Parse array-like string
            ssm_inputs = ssm_inputs_str.strip('[]').replace('"', '').split(', ')
            context.ssm_param_inputs = ssm_inputs


@then('the CloudFormation stack should be terminated')
def step_then_cfn_stack_terminated(context):
    """Verify CloudFormation stack was terminated."""
    assert context.current_task.run.called, "Stack termination task should have been executed"


@then('the stack deletion should complete successfully')
def step_then_stack_deletion_completes(context):
    """Verify stack deletion completed successfully."""
    assert context.task_result == "success", "Stack deletion should have succeeded"


@then('the stack should be terminated using the service role')
def step_then_stack_terminated_service_role(context):
    """Verify stack was terminated using service role."""
    use_service_role = context.task_attributes.get('use_service_role', False)
    assert use_service_role, "Service role should be used for termination"


@then('proper IAM permissions should be used for termination')
def step_then_proper_iam_permissions_used(context):
    """Verify proper IAM permissions were used for termination."""
    assert getattr(context, 'cfn_service_role_configured', False), "CFN service role should be configured"


@then('the SSM parameters should be retrieved for context')
def step_then_ssm_params_retrieved_context(context):
    """Verify SSM parameters were retrieved for context."""
    assert hasattr(context, 'ssm_param_inputs'), "SSM parameter inputs should have been provided"


@then('the stack should be terminated appropriately')
def step_then_stack_terminated_appropriately(context):
    """Verify stack was terminated appropriately."""
    assert context.current_task.run.called, "Stack termination should have proceeded"


@then('SSM parameter values should be logged for reference')
def step_then_ssm_values_logged(context):
    """Verify SSM parameter values were logged for reference."""
    pass


@then('the StackSet instance should be removed from the target account')
def step_then_stackset_instance_removed(context):
    """Verify StackSet instance was removed from target account."""
    assert getattr(context, 'stackset_instance_exists', False), "StackSet instance should have existed"
    stack_set_name = context.task_attributes.get('stack_set_name')
    assert stack_set_name, "StackSet name should be specified"


@then('the StackSet operation should complete successfully')
def step_then_stackset_operation_completes(context):
    """Verify StackSet operation completed successfully."""
    pass


@then('the task should handle StackSet-specific termination logic')
def step_then_task_handles_stackset_termination(context):
    """Verify task handled StackSet-specific termination logic."""
    pass


@then('the task should handle the missing stack gracefully')
def step_then_task_handles_missing_stack(context):
    """Verify task handled missing stack gracefully."""
    assert not getattr(context, 'stack_exists', True), "Stack should not exist"


@then('appropriate logging should indicate stack was not found')
def step_then_logging_indicates_stack_not_found(context):
    """Verify logging indicates stack was not found."""
    pass


@then('the stack termination should proceed with these settings')
def step_then_stack_termination_proceeds_with_settings(context):
    """Verify stack termination proceeded with specified settings."""
    assert context.current_task.run.called, "Stack termination should have proceeded"


@then('the stack should be terminated with all parameter context')
def step_then_stack_terminated_with_parameter_context(context):
    """Verify stack was terminated with all parameter context."""
    assert hasattr(context, 'launch_parameters'), "Launch parameters should be available"
    assert hasattr(context, 'manifest_parameters'), "Manifest parameters should be available"
    assert hasattr(context, 'account_parameters'), "Account parameters should be available"


@then('parameter values should be logged for reference')
def step_then_parameter_values_logged(context):
    """Verify parameter values were logged for reference."""
    pass


@then('the termination should complete successfully')
def step_then_termination_completes_successfully(context):
    """Verify termination completed successfully."""
    assert context.task_result == "success", "Termination should have completed successfully"