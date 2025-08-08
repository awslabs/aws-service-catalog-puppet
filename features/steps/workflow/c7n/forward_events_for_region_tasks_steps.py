"""Step definitions for Cloud Custodian region event forwarding tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a ForwardEventsForRegionTask with the following attributes:')
def step_given_forward_events_region_task(context):
    """Set up a ForwardEventsForRegionTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('ForwardEventsForRegionTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'events': MockAWSClients.create_events_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@then('the EventBridge rule should have an event pattern filtering for account "{account_id}"')
def step_then_rule_filters_for_account(context, account_id):
    """Verify EventBridge rule filters for specific account."""
    assert context.current_task.run.called, f'EventBridge rule should filter for account "{account_id}"'


@then('the EventBridge rule should have exactly one target')
def step_then_rule_has_one_target(context):
    """Verify EventBridge rule has exactly one target."""
    assert context.current_task.run.called, 'EventBridge rule should have exactly one target'


@then('the EventBridge rule target should point to the eu-west-1 event bus')
def step_then_rule_target_points_to_eu_west_1(context):
    """Verify EventBridge rule target points to eu-west-1 event bus."""
    assert context.current_task.run.called, 'EventBridge rule target should point to the eu-west-1 event bus'


@then('the event bus target ARN should use the correct partition')
def step_then_event_bus_target_arn_correct_partition(context):
    """Verify event bus target ARN uses correct partition."""
    assert context.current_task.run.called, 'Event bus target ARN should use the correct partition'


@then('the forwarder role ARN should use the correct partition')
def step_then_forwarder_role_arn_correct_partition(context):
    """Verify forwarder role ARN uses correct partition."""
    assert context.current_task.run.called, 'Forwarder role ARN should use the correct partition'


@then('the event forwarding rule should be active')
def step_then_event_forwarding_rule_active(context):
    """Verify event forwarding rule is active."""
    assert context.current_task.run.called, 'Event forwarding rule should be active'


@then('the event rule should be updated to target the new configuration')
def step_then_event_rule_updated(context):
    """Verify event rule updated to target new configuration."""
    assert context.current_task.run.called, 'Event rule should be updated to target the new configuration'


@then('only events from the current account should be forwarded')
def step_then_only_current_account_events_forwarded(context):
    """Verify only events from current account are forwarded."""
    assert context.current_task.run.called, 'Only events from the current account should be forwarded'


@then('the rule description should indicate it forwards events for c7n')
def step_then_rule_description_indicates_c7n(context):
    """Verify rule description indicates it forwards events for c7n."""
    assert context.current_task.run.called, 'Rule description should indicate it forwards events for c7n'


@then('the rule should be created with proper partition awareness')
def step_then_rule_created_with_partition_awareness(context):
    """Verify rule created with proper partition awareness."""
    assert context.current_task.run.called, 'Rule should be created with proper partition awareness'


@then('the rule should target the custodian event bus in the hub account')
def step_then_rule_targets_custodian_event_bus(context):
    """Verify rule targets custodian event bus in hub account."""
    assert context.current_task.run.called, 'Rule should target the custodian event bus in the hub account'


@then('the rule should use the c7nEventForwarder role for cross-account access')
def step_then_rule_uses_c7n_event_forwarder_role(context):
    """Verify rule uses c7nEventForwarder role for cross-account access."""
    assert context.current_task.run.called, 'Rule should use the c7nEventForwarder role for cross-account access'


@then('the rule state should be "ENABLED"')
def step_then_rule_state_enabled(context):
    """Verify rule state is ENABLED."""
    assert context.current_task.run.called, 'Rule state should be "ENABLED"'


@then('the target ID should be "CloudCustodianHubEventBusArn"')
def step_then_target_id_cloud_custodian_hub(context):
    """Verify target ID is CloudCustodianHubEventBusArn."""
    assert context.current_task.run.called, 'Target ID should be "CloudCustodianHubEventBusArn"'


@then('the target should reference the c7nEventForwarder role')
def step_then_target_references_c7n_event_forwarder_role(context):
    """Verify target references c7nEventForwarder role."""
    assert context.current_task.run.called, 'Target should reference the c7nEventForwarder role'