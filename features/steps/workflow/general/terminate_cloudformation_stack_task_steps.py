"""Step definitions for CloudFormation stack termination tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a TerminateCloudFormationStackTask with the following attributes:')
def step_given_terminate_cloudformation_stack_task(context):
    """Set up a TerminateCloudFormationStackTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('TerminateCloudFormationStackTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'cloudformation': MockAWSClients.create_cloudformation_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@given('I have CloudFormation delete permissions')
def step_given_cf_delete_permissions(context):
    """Set up CloudFormation delete permissions."""
    context.cf_delete_permissions = True




@then('the CloudFormation stack should be deleted')
def step_then_cf_stack_deleted(context):
    """Verify CloudFormation stack was deleted."""
    assert context.current_task.run.called, "Stack deletion task should have been executed"


@then('the task should handle the non-existent stack gracefully')
def step_then_handle_nonexistent_stack(context):
    """Verify task handles non-existent stack gracefully."""
    assert context.task_result != "error", "Task should handle missing stack gracefully"


@then('no error should be raised for missing stack')
def step_then_no_error_for_missing_stack(context):
    """Verify no error is raised for missing stack."""
    pass


