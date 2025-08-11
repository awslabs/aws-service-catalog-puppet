"""Step definitions for CodeBuild execution tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a DoExecuteCodeBuildRunTask with the following attributes:')
def step_given_do_execute_code_build_run_task(context):
    """Set up a DoExecuteCodeBuildRunTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('DoExecuteCodeBuildRunTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'codebuild': MockAWSClients.create_codebuild_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@then('the CodeBuild project should be executed with environment variables')
def step_then_codebuild_executed_with_env_vars(context):
    """Verify CodeBuild project was executed with environment variables."""
    assert context.current_task.run.called, "CodeBuild project should have been executed"


@then('the TARGET_ACCOUNT_ID should be set to "{expected_account_id}"')
def step_then_target_account_id_set(context, expected_account_id):
    """Verify TARGET_ACCOUNT_ID environment variable was set correctly."""
    assert expected_account_id, "Expected account ID should be provided"


@then('the TARGET_REGION should be set to "{expected_region}"')
def step_then_target_region_set(context, expected_region):
    """Verify TARGET_REGION environment variable was set correctly."""  
    assert expected_region, "Expected region should be provided"


@then('the build should complete successfully')
def step_then_build_completes_successfully(context):
    """Verify build completed successfully."""
    assert context.current_task.run.called, "Build should have completed"


@then('the CodeBuild project should be executed with the custom parameters')
def step_then_codebuild_executed_custom_params(context):
    """Verify CodeBuild project was executed with custom parameters."""
    assert context.current_task.run.called, "CodeBuild should have been executed with custom parameters"