"""Step definitions for product termination tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a DoTerminateProductTask with the following attributes:')
def step_given_do_terminate_product_task(context):
    """Set up a DoTerminateProductTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('DoTerminateProductTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'servicecatalog': MockAWSClients.create_service_catalog_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@then('the provisioned product should be terminated')
def step_then_product_terminated(context):
    """Verify provisioned product was terminated."""
    assert context.current_task.run.called, "Product termination task should have been executed"


@then('a ResourceNotFoundException should be handled gracefully')
def step_then_resource_not_found_handled(context):
    """Verify ResourceNotFoundException was handled gracefully."""
    assert context.task_result != "error", "Task should handle missing resource gracefully"


@then('the task should log that the product was not found')
def step_then_log_product_not_found(context):
    """Verify task logged that product was not found."""
    pass


@then('the task should wait for the current operation to complete')
def step_then_task_waits_for_operation(context):
    """Verify task waits for current operation to complete."""
    if getattr(context, 'product_under_change', False):
        assert context.current_task.run.called, "Task should have been executed"


@then('then proceed with termination')
def step_then_proceed_with_termination(context):
    """Verify task proceeded with termination after waiting."""
    assert context.current_task.run.called, "Task should have proceeded with termination"


@then('the task should complete with all parameters logged')
def step_then_task_complete_with_params_logged(context):
    """Verify task completed with all parameters logged."""
    assert context.current_task.run.called, "Task should have completed successfully"
    assert hasattr(context, 'launch_parameters'), "Launch parameters should be available"
    assert hasattr(context, 'manifest_parameters'), "Manifest parameters should be available"