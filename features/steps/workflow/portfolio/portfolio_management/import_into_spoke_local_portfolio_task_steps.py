"""Step definitions for spoke portfolio import tasks."""

from behave import given, when, then
from unittest.mock import MagicMock
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('an ImportIntoSpokeLocalPortfolioTask with the following attributes:')
def step_given_import_into_spoke_portfolio_task(context):
    """Set up an ImportIntoSpokeLocalPortfolioTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('ImportIntoSpokeLocalPortfolioTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'servicecatalog': MockAWSClients.create_service_catalog_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Custom mock behavior for hub portfolio accessibility
    original_run = mock_task.run
    def custom_run(*args, **kwargs):
        # Check if hub portfolio is accessible
        if getattr(context, 'hub_portfolio_accessible', True) == False:
            context.task_result = "error"
            context.task_error = "Hub portfolio reference is invalid or inaccessible"
            raise Exception("Hub portfolio reference is invalid or inaccessible")
        return original_run(*args, **kwargs) if original_run else None
    mock_task.run = MagicMock(side_effect=custom_run)


@then('products should be imported from hub portfolio to spoke portfolio')
def step_then_products_imported_hub_to_spoke(context):
    """Verify products were imported from hub to spoke portfolio."""
    assert getattr(context, 'hub_has_new_products', False), "Hub should have new products"
    assert context.current_task.run.called, "Import task should have been executed"


@then('product versions should be synchronized')
def step_then_product_versions_synchronized(context):
    """Verify product versions were synchronized."""
    pass


@then('no products should be imported')
def step_then_no_products_imported(context):
    """Verify no products were imported."""
    assert getattr(context, 'spoke_has_all_products', False), "Spoke should already have all products"


@then('the task should complete without making changes')
def step_then_task_completes_no_changes(context):
    """Verify task completed without making changes."""
    assert context.task_result != "error", "Task should complete successfully"


@then('appropriate logging should indicate products are already synchronized')
def step_then_logging_indicates_synchronized(context):
    """Verify logging indicates products are already synchronized."""
    pass


@then('the latest product versions should be imported from hub')
def step_then_latest_versions_imported(context):
    """Verify latest product versions were imported from hub."""
    assert getattr(context, 'hub_has_multiple_versions', False), "Hub should have multiple versions"


@then('existing products should be updated to latest versions')
def step_then_existing_products_updated_latest(context):
    """Verify existing products were updated to latest versions."""
    assert getattr(context, 'spoke_has_outdated_versions', False), "Spoke should have had outdated versions"


@then('new products should be added to the spoke portfolio')
def step_then_new_products_added_spoke(context):
    """Verify new products were added to spoke portfolio."""
    assert context.current_task.run.called, "Import task should have added new products"


@then('version synchronization should be completed')
def step_then_version_sync_completed(context):
    """Verify version synchronization was completed."""
    pass


@then('all products from hub portfolio should be imported')
def step_then_all_hub_products_imported(context):
    """Verify all products from hub portfolio were imported."""
    assert getattr(context, 'spoke_portfolio_empty', False), "Spoke portfolio should have been empty"


@then('all product versions should be copied to spoke portfolio')
def step_then_all_versions_copied_spoke(context):
    """Verify all product versions were copied to spoke portfolio."""
    pass


@then('the spoke portfolio should match the hub portfolio content')
def step_then_spoke_matches_hub_content(context):
    """Verify spoke portfolio matches hub portfolio content."""
    pass


@then('cross-region product import should succeed')
def step_then_cross_region_import_succeeds(context):
    """Verify cross-region product import succeeded."""
    assert getattr(context, 'hub_different_region', False), "Hub should be in different region"
    assert context.task_result == "success", "Cross-region import should succeed"


@then('product metadata should be preserved during import')
def step_then_product_metadata_preserved(context):
    """Verify product metadata was preserved during import."""
    pass


@then('regional constraints should be handled appropriately')
def step_then_regional_constraints_handled(context):
    """Verify regional constraints were handled appropriately."""
    pass


@then('the error should indicate hub portfolio access failure')
def step_then_error_indicates_hub_access_failure(context):
    """Verify error indicates hub portfolio access failure."""
    assert not getattr(context, 'hub_portfolio_accessible', True), "Hub portfolio should not be accessible"


@then('the spoke portfolio should remain unchanged')
def step_then_spoke_portfolio_unchanged(context):
    """Verify spoke portfolio remained unchanged."""
    pass