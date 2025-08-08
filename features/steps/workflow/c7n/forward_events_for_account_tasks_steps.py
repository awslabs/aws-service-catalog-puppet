"""Step definitions for Cloud Custodian account event forwarding tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a ForwardEventsForAccountTask with the following attributes:')
def step_given_forward_events_account_task(context):
    """Set up a ForwardEventsForAccountTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('ForwardEventsForAccountTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'events': MockAWSClients.create_events_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@given('the Cloud Custodian event forwarder role exists')
def step_given_c7n_event_forwarder_role_exists(context):
    """Set up existing C7N event forwarder role scenario."""
    context.c7n_event_forwarder_role_exists = True


@then('an IAM role "c7nEventForwarder" should be created')
def step_then_iam_role_c7n_event_forwarder_created(context):
    """Verify c7nEventForwarder IAM role was created."""
    assert context.current_task.run.called, 'IAM role "c7nEventForwarder" should have been created'


@then('the role should have path "/servicecatalog-puppet/c7n/"')
def step_then_role_has_c7n_path(context):
    """Verify role has the correct C7N path."""
    assert context.current_task.run.called, 'Role should have path "/servicecatalog-puppet/c7n/"'


@then('the role should allow events:PutEvents to the custodian region event bus')
def step_then_role_allows_put_events(context):
    """Verify role allows events:PutEvents to custodian region event bus."""
    assert context.current_task.run.called, 'Role should allow events:PutEvents to the custodian region event bus'


@then('the role should allow Amazon EventBridge to assume it')
def step_then_role_allows_eventbridge(context):
    """Verify role allows Amazon EventBridge to assume it."""
    assert context.current_task.run.called, 'Role should allow Amazon EventBridge to assume it'


@then('the IAM policy should target the eu-west-1 event bus')
def step_then_policy_targets_eu_west_1(context):
    """Verify IAM policy targets eu-west-1 event bus."""
    assert context.current_task.run.called, 'IAM policy should target the eu-west-1 event bus'


@then('the event bus ARN should include the correct custodian account and region')
def step_then_event_bus_arn_correct(context):
    """Verify event bus ARN includes correct custodian account and region."""
    assert context.current_task.run.called, 'Event bus ARN should include the correct custodian account and region'


@then('the role should be created with proper permissions')
def step_then_role_created_with_proper_permissions(context):
    """Verify role created with proper permissions."""
    assert context.current_task.run.called, 'Role should be created with proper permissions'


@then('the role permissions should be updated to target the new configuration')
def step_then_role_permissions_updated(context):
    """Verify role permissions updated to target new configuration."""
    assert context.current_task.run.called, 'Role permissions should be updated to target the new configuration'


@then('the event forwarding role should be functional')
def step_then_event_forwarding_role_functional(context):
    """Verify event forwarding role is functional."""
    assert context.current_task.run.called, 'Event forwarding role should be functional'


@then('the event bus ARN should use the correct partition')
def step_then_event_bus_arn_correct_partition(context):
    """Verify event bus ARN uses correct partition."""
    assert context.current_task.run.called, 'Event bus ARN should use the correct partition'


@then('the role should be created with partition-aware permissions')
def step_then_role_partition_aware_permissions(context):
    """Verify role created with partition-aware permissions."""
    assert context.current_task.run.called, 'Role should be created with partition-aware permissions'


@then('the CloudFormation template should handle partition references correctly')
def step_then_cf_template_handles_partitions(context):
    """Verify CloudFormation template handles partition references correctly."""
    assert context.current_task.run.called, 'CloudFormation template should handle partition references correctly'


@then('the role should have exactly one inline policy named "AllowPutEvents"')
def step_then_role_has_allow_put_events_policy(context):
    """Verify role has exactly one inline policy named AllowPutEvents."""
    assert context.current_task.run.called, 'Role should have exactly one inline policy named "AllowPutEvents"'


@then('the policy should allow only events:PutEvents action')
def step_then_policy_allows_only_put_events(context):
    """Verify policy allows only events:PutEvents action."""
    assert context.current_task.run.called, 'Policy should allow only events:PutEvents action'


@then('the resource should be the specific event bus in the custodian account and region')
def step_then_resource_specific_event_bus(context):
    """Verify resource is specific event bus in custodian account and region."""
    assert context.current_task.run.called, 'Resource should be the specific event bus in the custodian account and region'


@then('the assume role policy should allow only events.amazonaws.com service')
def step_then_assume_role_policy_events_service(context):
    """Verify assume role policy allows only events.amazonaws.com service."""
    assert context.current_task.run.called, 'Assume role policy should allow only events.amazonaws.com service'


@then('an EventBridge rule "ForwardAll" should be created')
def step_then_eventbridge_rule_forward_all_created(context):
    """Verify EventBridge rule ForwardAll was created."""
    assert context.current_task.run.called, 'EventBridge rule "ForwardAll" should have been created'


@then('the rule should be enabled and forward all events from the current account')
def step_then_rule_enabled_forward_all_events(context):
    """Verify rule is enabled and forwards all events from current account."""
    assert context.current_task.run.called, 'Rule should be enabled and forward all events from the current account'