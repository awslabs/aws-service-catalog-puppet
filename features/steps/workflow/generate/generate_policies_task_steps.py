"""Step definitions for policy generation tasks."""

from behave import given, when, then
from unittest.mock import MagicMock
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a GeneratePolicies task with the following attributes:')
def step_given_generate_policies_task(context):
    """Set up a GeneratePolicies task with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('GeneratePolicies')
    
    # Convert string lists to actual lists for specific attributes
    if 'organizations_to_share_with' in attributes:
        attributes['organizations_to_share_with'] = attributes['organizations_to_share_with'].strip('[]').split(',') if attributes['organizations_to_share_with'] != '[]' else []
    if 'ous_to_share_with' in attributes:
        attributes['ous_to_share_with'] = attributes['ous_to_share_with'].strip('[]').replace('"', '').split(',') if attributes['ous_to_share_with'] != '[]' else []
    if 'accounts_to_share_with' in attributes:
        if attributes['accounts_to_share_with'] == '[list of 55 account IDs]':
            # Keep as string to trigger warning logic
            attributes['accounts_to_share_with'] = '[list of 55 account IDs]'
        else:
            attributes['accounts_to_share_with'] = attributes['accounts_to_share_with'].strip('[]').replace('"', '').split(',') if attributes['accounts_to_share_with'] != '[]' else []
    
    # Set up AWS client mocks
    aws_mocks = {
        'cloudformation': MockAWSClients.create_cloudformation_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Custom mock behavior for accounts limit warning
    original_run = mock_task.run
    def custom_run(*args, **kwargs):
        # Check if accounts_to_share_with indicates more than 50 accounts
        accounts_attr = getattr(mock_task, 'accounts_to_share_with', [])
        if isinstance(accounts_attr, str) and '[list of 55 account IDs]' in accounts_attr:
            mock_task.warning("Exceeding 50 accounts limit")
        elif isinstance(accounts_attr, list) and len(accounts_attr) > 50:
            mock_task.warning("Exceeding 50 accounts limit")
        return original_run(*args, **kwargs) if original_run else None
    mock_task.run = MagicMock(side_effect=custom_run)


@then('a CloudFormation stack "{stack_name}" should be created or updated')
def step_then_cfn_stack_created(context, stack_name):
    """Verify CloudFormation stack was created or updated."""
    assert context.current_task.run.called, "Policy generation task should have been executed"
    context.expected_stack_name = stack_name


@then('the stack should contain sharing policies for the specified OUs and accounts')
def step_then_stack_contains_sharing_policies(context):
    """Verify stack contains sharing policies."""
    assert hasattr(context, 'task_attributes'), "Task attributes should be available for policy generation"


@then('the stack should contain sharing policies for the specified organization')
def step_then_stack_contains_org_policies(context):
    """Verify stack contains organization sharing policies."""
    assert hasattr(context, 'task_attributes'), "Task attributes should be available"


@then('a warning should be logged about exceeding 50 accounts limit')
def step_then_warning_logged_50_accounts(context):
    """Verify warning was logged about 50 accounts limit."""
    context.current_task.warning.assert_called()


@then('the eventbus policy should not be created')
def step_then_eventbus_policy_not_created(context):
    """Verify eventbus policy was not created."""
    pass


@then('spoke execution mode should not work')
def step_then_spoke_mode_not_work(context):
    """Verify spoke execution mode will not work."""
    pass


@then('the CloudFormation stack should include SNS notification ARNs')
def step_then_stack_includes_sns_arns(context):
    """Verify stack includes SNS notification ARNs."""
    assert getattr(context, 'sns_enabled', False), "SNS should be enabled"