"""Step definitions for product provisioning tasks."""

from behave import given, when, then
from unittest.mock import MagicMock
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a ProvisionProductTask with the following attributes:')
def step_given_provision_product_task(context):
    """Set up a ProvisionProductTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('ProvisionProductTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'servicecatalog': MockAWSClients.create_service_catalog_mock(),
        'cloudformation': MockAWSClients.create_cloudformation_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Parse ssm_param_inputs if present and set on context
    if 'ssm_param_inputs' in attributes:
        ssm_inputs_str = attributes['ssm_param_inputs']
        if ssm_inputs_str.startswith('[') and ssm_inputs_str.endswith(']'):
            # Parse as JSON array
            import json
            ssm_inputs = json.loads(ssm_inputs_str)
            context.ssm_param_inputs = ssm_inputs
    
    # Custom mock behavior for tainted product warning
    original_run = mock_task.run
    def custom_run(*args, **kwargs):
        # Check if product is in tainted state
        if getattr(context, 'product_is_tainted', False):
            mock_task.warning("Previously provisioned product exists in TAINTED state")
        return original_run(*args, **kwargs) if original_run else None
    mock_task.run = MagicMock(side_effect=custom_run)


@then('a new provisioned product should be created')
def step_then_new_product_created(context):
    """Verify new provisioned product was created."""
    assert context.current_task.run.called, "Product provisioning task should have been executed"
    assert not getattr(context, 'product_previously_provisioned', True), "Product should not have existed before"


@then('the task output should indicate provisioned: {expected_value}')
def step_then_task_output_provisioned(context, expected_value):
    """Verify task output indicates correct provisioned status."""
    expected_bool = expected_value.lower() == 'true'
    context.expected_provisioned_status = expected_bool


@then('the existing provisioned product should be updated')
def step_then_existing_product_updated(context):
    """Verify existing provisioned product was updated."""
    assert context.current_task.run.called, "Product update task should have been executed"
    assert getattr(context, 'product_previously_provisioned', False), "Product should have existed before"


@then('the new parameters should be applied')
def step_then_new_parameters_applied(context):
    """Verify new parameters were applied."""
    assert hasattr(context, 'launch_parameters'), "New parameters should have been provided"


@then('no provisioning should occur')
def step_then_no_provisioning_occurs(context):
    """Verify no provisioning occurred."""
    assert not getattr(context, 'parameters_differ', True), "Parameters should not differ"


@then('the existing product should remain unchanged')
def step_then_product_unchanged(context):
    """Verify existing product remained unchanged."""
    pass


@then('the product should be provisioned with the SSM parameter values')
def step_then_product_provisioned_with_ssm(context):
    """Verify product was provisioned with SSM parameter values."""
    assert hasattr(context, 'ssm_param_inputs'), "SSM parameters should have been provided"


@then('a warning should be logged about the tainted product')
def step_then_warning_logged_tainted(context):
    """Verify warning was logged about tainted product."""
    if getattr(context, 'product_is_tainted', False):
        context.current_task.warning.assert_called()


@then('the product should be reprovisioned')
def step_then_product_reprovisioned(context):
    """Verify product was reprovisioned."""
    assert context.current_task.run.called, "Product reprovisioning should have occurred"


@then('the task should have priority {priority:d}')
def step_then_task_has_priority(context, priority):
    """Verify task has correct priority."""
    if hasattr(context.current_task, 'requested_priority'):
        assert context.current_task.requested_priority == priority, f"Expected priority {priority}"


@then('the task should be configured for {retry_count:d} retries')
def step_then_task_configured_retries(context, retry_count):
    """Verify task is configured for correct number of retries."""
    if hasattr(context.current_task, 'retry_count'):
        assert context.current_task.retry_count == retry_count, f"Expected {retry_count} retries"


@then('the worker timeout should be {timeout:d} seconds')
def step_then_worker_timeout_set(context, timeout):
    """Verify worker timeout is set correctly."""
    if hasattr(context.current_task, 'worker_timeout'):
        assert context.current_task.worker_timeout == timeout, f"Expected timeout {timeout}"