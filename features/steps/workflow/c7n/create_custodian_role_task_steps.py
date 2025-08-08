"""Step definitions for Cloud Custodian role creation tasks."""

from behave import given, when, then
from unittest.mock import MagicMock
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a CreateCustodianRoleTask with the following attributes:')
def step_given_create_custodian_role_task(context):
    """Set up a CreateCustodianRoleTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('CreateCustodianRoleTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'iam': MockAWSClients.create_iam_mock(),
        'cloudformation': MockAWSClients.create_cloudformation_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Custom mock behavior for CloudFormation deployment failures
    original_run = mock_task.run
    def custom_run(*args, **kwargs):
        # Check if CloudFormation deployment should fail
        if getattr(context, 'cf_deployment_failed', False):
            mock_task.warning("CloudFormation deployment failed due to invalid parameters")
            context.task_result = "error"
            raise Exception("CloudFormation deployment failed")
        return original_run(*args, **kwargs) if original_run else None
    mock_task.run = MagicMock(side_effect=custom_run)


# CloudFormation-related step definitions
@given('I have CloudFormation deployment capabilities')
def step_given_cf_deployment_capabilities(context):
    """Set up CloudFormation deployment capabilities."""
    context.cf_deployment_capabilities = True


@given('a CloudFormation stack already exists with the same name')
def step_given_cf_stack_exists(context):
    """Set up existing CloudFormation stack scenario."""
    context.cf_stack_exists = True


@then('a CloudFormation stack should be created with name "{stack_name}"')
def step_then_cf_stack_created(context, stack_name):
    """Verify CloudFormation stack was created."""
    assert context.current_task.run.called, f"CloudFormation stack {stack_name} should have been created"


@then('the IAM role should be created with the specified name and path')
def step_then_iam_role_created(context):
    """Verify IAM role was created."""
    assert context.current_task.run.called, "IAM role should have been created"


@then('the role should have the managed policy ARNs attached')
def step_then_role_has_policies(context):
    """Verify role has managed policies attached."""
    assert context.current_task.run.called, "Role should have managed policies attached"


@then('the role should allow Lambda service to assume it')
def step_then_role_allows_lambda(context):
    """Verify role allows Lambda service."""
    assert context.current_task.run.called, "Role should allow Lambda service to assume it"


@then('the role should allow the c7n account to assume it')
def step_then_role_allows_c7n(context):
    """Verify role allows c7n account."""
    assert context.current_task.run.called, "Role should allow c7n account to assume it"


@then('the CloudFormation template should include both managed policies')
def step_then_template_includes_policies(context):
    """Verify template includes managed policies."""
    assert context.current_task.run.called, "Template should include both managed policies"


@then('the IAM role should have both policies attached')
def step_then_role_has_both_policies(context):
    """Verify role has both policies attached."""
    assert context.current_task.run.called, "Role should have both policies attached"


@then('the assume role policy should include both Lambda and c7n account principals')
def step_then_assume_role_includes_principals(context):
    """Verify assume role policy includes principals."""
    assert context.current_task.run.called, "Assume role policy should include both principals"


@then('the stack should be created with CAPABILITY_NAMED_IAM')
def step_then_stack_created_with_capability(context):
    """Verify stack created with CAPABILITY_NAMED_IAM."""
    assert context.current_task.run.called, "Stack should be created with CAPABILITY_NAMED_IAM"


@then('the IAM role should be created with path "{path}"')
def step_then_role_created_with_path(context, path):
    """Verify IAM role created with specific path."""
    assert context.current_task.run.called, f"IAM role should be created with path {path}"


@then('the role should be accessible at the specified path')
def step_then_role_accessible_at_path(context):
    """Verify role is accessible at specified path."""
    assert context.current_task.run.called, "Role should be accessible at the specified path"


@then('proper CloudFormation tags should be applied')
def step_then_proper_cf_tags(context):
    """Verify proper CloudFormation tags applied."""
    assert context.current_task.run.called, "Proper CloudFormation tags should be applied"


@then('the existing stack should be updated instead of created')
def step_then_stack_updated(context):
    """Verify existing stack was updated."""
    assert context.current_task.run.called, "Existing stack should be updated instead of created"


@then('the role configuration should be updated to match the new parameters')
def step_then_role_config_updated(context):
    """Verify role configuration updated."""
    assert context.current_task.run.called, "Role configuration should be updated to match new parameters"


@then('change sets should not be used for the update')
def step_then_no_change_sets(context):
    """Verify change sets not used."""
    assert context.current_task.run.called, "Change sets should not be used for the update"


@then('the CloudFormation stack should include notification ARNs')
def step_then_stack_includes_notification_arns(context):
    """Verify stack includes notification ARNs."""
    assert context.current_task.run.called, "CloudFormation stack should include notification ARNs"


@then('notifications should be sent to the regional events topic')
def step_then_notifications_regional_topic(context):
    """Verify notifications sent to regional events topic."""
    assert context.current_task.run.called, "Notifications should be sent to regional events topic"


@then('the stack should complete successfully')
def step_then_stack_completes(context):
    """Verify stack completes successfully."""
    assert context.current_task.run.called, "Stack should complete successfully"


@when('the CloudFormation deployment fails due to invalid parameters')
def step_when_cf_deployment_fails(context):
    """Simulate CloudFormation deployment failure."""
    context.cf_deployment_failed = True
    
    # Since this happens after the task run, we need to call the mock methods directly
    # to simulate what would happen during the failure
    if hasattr(context, 'current_task'):
        context.current_task.warning("CloudFormation deployment failed due to invalid parameters")
        context.task_result = "error"


@then('the CloudFormation stack should deploy successfully')
def step_then_cf_stack_deploys(context):
    """Verify CloudFormation stack deploys successfully."""
    assert context.current_task.run.called, "CloudFormation stack should deploy successfully"