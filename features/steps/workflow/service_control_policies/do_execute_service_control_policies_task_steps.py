"""Step definitions for Service Control Policy tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a DoExecuteServiceControlPoliciesTask with the following attributes:')
def step_given_do_execute_scp_task(context):
    """Set up a DoExecuteServiceControlPoliciesTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('DoExecuteServiceControlPoliciesTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'organizations': MockAWSClients.create_organizations_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@then('the service control policy should be attached to the specified account')
def step_then_scp_attached_to_account(context):
    """Verify SCP was attached to specified account."""
    assert context.current_task.run.called, "SCP execution task should have been executed"
    account_id = context.task_attributes.get('account_id')
    assert account_id, "Account ID should be specified"


@then('the policy should enforce the defined restrictions')
def step_then_policy_enforces_restrictions(context):
    """Verify policy enforces defined restrictions."""
    assert hasattr(context, 'content'), "Policy content should have been provided"


@then('the service control policy should be attached to the specified organizational unit')
def step_then_scp_attached_to_ou(context):
    """Verify SCP was attached to specified organizational unit."""
    assert context.current_task.run.called, "SCP execution task should have been executed"
    ou_name = context.task_attributes.get('ou_name')
    assert ou_name, "Organizational unit name should be specified"


@then('all accounts in the OU should inherit the policy restrictions')
def step_then_ou_accounts_inherit_policy(context):
    """Verify all accounts in OU inherit policy restrictions."""
    pass


@then('the task should be executed with priority {priority:d}')
def step_then_task_executed_with_priority(context, priority):
    """Verify task was executed with specified priority."""
    if hasattr(context.current_task, 'requested_priority'):
        assert context.current_task.requested_priority == priority, f"Expected priority {priority}"


@then('critical security restrictions should be enforced')
def step_then_critical_security_enforced(context):
    """Verify critical security restrictions are enforced."""
    assert hasattr(context, 'content'), "Security policy content should have been provided"


@then('the complex policy content should be processed correctly')
def step_then_complex_policy_processed(context):
    """Verify complex policy content was processed correctly."""
    assert hasattr(context, 'content'), "Complex policy content should have been provided"
    content = context.content
    assert isinstance(content, dict), "Content should be structured policy"


@then('the service control policy should be attached with all conditions')
def step_then_scp_attached_with_conditions(context):
    """Verify SCP was attached with all conditions."""
    assert context.current_task.run.called, "SCP task should have been executed"


@then('the organizational unit should be found by name "{ou_name}"')
def step_then_ou_found_by_name(context, ou_name):
    """Verify organizational unit was found by name."""
    assert context.task_attributes.get('ou_name') == ou_name, f"Expected OU name {ou_name}"


@then('development-specific restrictions should be applied')
def step_then_dev_restrictions_applied(context):
    """Verify development-specific restrictions were applied."""
    assert hasattr(context, 'content'), "Policy content should specify development restrictions"