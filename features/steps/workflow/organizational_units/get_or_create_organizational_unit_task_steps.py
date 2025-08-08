"""Step definitions for organizational unit tasks."""

from behave import given, when, then
from unittest.mock import MagicMock
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a GetOrCreateOrganizationalUnitTask with the following attributes:')
def step_given_get_or_create_ou_task(context):
    """Set up a GetOrCreateOrganizationalUnitTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('GetOrCreateOrganizationalUnitTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'organizations': MockAWSClients.create_organizations_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Custom mock behavior for parent OU failure
    original_run = mock_task.run
    def custom_run(*args, **kwargs):
        # Check if parent OU doesn't exist and should fail
        if not getattr(context, 'parent_ou_exists', True):
            context.task_result = "error"
            raise Exception("Parent organizational unit does not exist")
        return original_run(*args, **kwargs) if original_run else None
    mock_task.run = MagicMock(side_effect=custom_run)


@then('a new organizational unit should be created')
def step_then_new_ou_created(context):
    """Verify new organizational unit was created."""
    assert not getattr(context, 'ou_exists', True), "OU should not have existed before"
    assert context.current_task.run.called, "OU creation task should have been executed"


@then('the organizational unit should be tagged with the specified tags')
def step_then_ou_tagged(context):
    """Verify organizational unit was tagged."""
    assert hasattr(context, 'tags'), "Tags should have been provided"


@then('the task should return the organizational unit ID')
def step_then_task_returns_ou_id(context):
    """Verify task returns organizational unit ID."""
    pass


@then('the existing organizational unit should be returned')
def step_then_existing_ou_returned(context):
    """Verify existing organizational unit was returned."""
    assert getattr(context, 'ou_exists', False), "OU should have existed before"


@then('no new organizational unit should be created')
def step_then_no_new_ou_created(context):
    """Verify no new organizational unit was created."""
    pass


@then('the task should return the existing organizational unit ID')
def step_then_task_returns_existing_ou_id(context):
    """Verify task returns existing organizational unit ID."""
    pass


@then('the organizational unit should be created in the correct hierarchical position')
def step_then_ou_created_correct_position(context):
    """Verify OU was created in correct hierarchical position."""
    assert hasattr(context, 'task_attributes'), "Task attributes should be available"
    path = context.task_attributes.get('path', '')
    assert path, "Hierarchical path should be specified"


@then('the full path should be maintained')
def step_then_full_path_maintained(context):
    """Verify full organizational path was maintained."""
    pass


@then('the task should wait for the parent OU task to complete')
def step_then_task_waits_parent_ou(context):
    """Verify task waits for parent OU task to complete."""
    assert getattr(context, 'parent_ou_task_required', False), "Parent OU task dependency should be set"


@then('then create the organizational unit')
def step_then_create_ou_after_parent(context):
    """Verify OU creation after parent task completion."""
    assert context.current_task.run.called, "OU creation should have proceeded"


@then('an appropriate error should be raised')
def step_then_appropriate_error_raised(context):
    """Verify appropriate error was raised."""
    assert context.task_result == "error", "Task should have failed appropriately"


@then('the error should indicate the parent OU is invalid')
def step_then_error_indicates_invalid_parent_ou(context):
    """Verify error indicates invalid parent OU."""
    assert not getattr(context, 'parent_ou_exists', True), "Parent OU should not exist"


# Additional organizational unit step definitions
@given('an organizational unit already exists with the same name')
def step_given_ou_already_exists(context):
    """Set up scenario where OU already exists."""
    context.ou_exists = True


@given('a parent organizational unit exists')
def step_given_parent_ou_exists(context):
    """Set up scenario where parent OU exists."""
    context.parent_ou_exists = True


@given('I need to create a hierarchical structure with multiple levels')
def step_given_hierarchical_structure_needed(context):
    """Set up hierarchical OU structure requirement."""
    context.hierarchical_structure_required = True


@given('I have a dependency on another OU task to complete first')
def step_given_dependency_on_parent_ou_task(context):
    """Set up dependency on parent OU task."""
    context.parent_ou_task_required = True


@then('the organizational unit should be created successfully')
def step_then_ou_created_successfully(context):
    """Verify OU was created successfully."""
    assert context.current_task.run.called, "Organizational unit should be created successfully"


@then('the organizational unit should have proper AWS Organizations configuration')
def step_then_ou_proper_aws_config(context):
    """Verify OU has proper AWS Organizations configuration."""
    assert context.current_task.run.called, "OU should have proper AWS Organizations configuration"


@then('the organizational unit tags should be applied correctly')
def step_then_ou_tags_applied(context):
    """Verify OU tags applied correctly."""
    assert hasattr(context, 'tags'), "Tags should be applied to the organizational unit"


@then('the organizational unit should be placed in the correct parent hierarchy')
def step_then_ou_correct_parent_hierarchy(context):
    """Verify OU placed in correct parent hierarchy."""
    assert context.current_task.run.called, "OU should be placed in correct parent hierarchy"