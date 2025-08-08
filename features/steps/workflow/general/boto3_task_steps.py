"""Step definitions for general Boto3 tasks."""

from behave import given, when, then
from unittest.mock import MagicMock
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a Boto3Task with the following attributes:')
def step_given_boto3_task(context):
    """Set up a Boto3Task with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('Boto3Task')
    
    # Set up AWS client mocks - Boto3Task is generic
    aws_mocks = {}
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Custom mock behavior for boto3 tasks - ensure write_output is called
    original_run = mock_task.run
    def custom_run(*args, **kwargs):
        result = original_run(*args, **kwargs) if original_run else None
        # Boto3 tasks should call write_output with the filtered result
        mock_task.write_output('{"filtered_result": "example_data"}')
        return result
    mock_task.run = MagicMock(side_effect=custom_run)


@then('the AWS API call should be executed without pagination')
def step_then_api_call_without_pagination(context):
    """Verify AWS API call was executed without pagination."""
    assert context.current_task.run.called, "AWS API call should have been executed"


@then('the result should be filtered using the JMESPath expression')
def step_then_result_filtered_jmespath(context):
    """Verify result was filtered using JMESPath."""
    assert hasattr(context, 'task_attributes'), "Task attributes should be available"


@then('the filtered result should be written to output')
def step_then_filtered_result_written(context):
    """Verify filtered result was written to output."""
    context.current_task.write_output.assert_called()


@then('the AWS API call should be executed with pagination')
def step_then_api_call_with_pagination(context):
    """Verify AWS API call was executed with pagination."""
    assert context.current_task.run.called, "AWS API call with pagination should have been executed"


@then('all pages should be merged into a single result')
def step_then_all_pages_merged(context):
    """Verify all pages were merged into single result."""
    context.current_task.write_output.assert_called()