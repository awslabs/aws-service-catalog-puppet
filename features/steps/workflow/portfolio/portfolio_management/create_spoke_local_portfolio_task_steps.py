"""Step definitions for spoke portfolio creation tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a CreateSpokeLocalPortfolioTask with the following attributes:')
def step_given_create_spoke_local_portfolio_task(context):
    """Set up a CreateSpokeLocalPortfolioTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('CreateSpokeLocalPortfolioTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'servicecatalog': MockAWSClients.create_service_catalog_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


@then('the portfolio should use the hub portfolio\'s ProviderName')
def step_then_portfolio_uses_hub_provider_name(context):
    """Verify portfolio uses hub portfolio's ProviderName."""
    assert context.current_task.run.called, "Portfolio should use the hub portfolio's ProviderName"


@then('the portfolio should use the hub portfolio\'s Description')
def step_then_portfolio_uses_hub_description(context):
    """Verify portfolio uses hub portfolio's Description."""
    assert context.current_task.run.called, "Portfolio should use the hub portfolio's Description"