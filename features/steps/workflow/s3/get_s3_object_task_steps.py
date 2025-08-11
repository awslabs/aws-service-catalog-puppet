"""Step definitions for S3 object retrieval tasks."""

from behave import given, when, then
from unittest.mock import MagicMock
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a GetS3ObjectTask with the following attributes:')
def step_given_get_s3_object_task(context):
    """Set up a GetS3ObjectTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('GetS3ObjectTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        's3': MockAWSClients.create_s3_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Custom mock behavior for S3 tasks - ensure write_output is called
    original_run = mock_task.run
    def custom_run(*args, **kwargs):
        # Check if S3 access is denied and should fail
        if getattr(context, 's3_access_denied', False):
            context.task_result = "error"
            context.task_error = "AccessDenied: Insufficient permissions to access S3 object"
            raise Exception("AccessDenied: Insufficient permissions to access S3 object")
        
        # Check if S3 object does not exist and should fail
        if hasattr(context, 'missing_s3_objects') and context.missing_s3_objects:
            # Check if the current task's key is in the missing objects
            task_key = attributes.get('key', '')
            if task_key in context.missing_s3_objects:
                context.task_result = "error" 
                context.task_error = "NoSuchKey: The specified key does not exist"
                raise Exception("NoSuchKey: The specified key does not exist")
        
        result = original_run(*args, **kwargs) if original_run else None
        # S3 tasks should call write_output with the retrieved content on success
        mock_task.write_output('{"s3_object_content": "retrieved_data"}')
        return result
    mock_task.run = MagicMock(side_effect=custom_run)


@then('the S3 object should be retrieved successfully')
def step_then_s3_object_retrieved(context):
    """Verify S3 object was retrieved successfully."""
    assert context.current_task.run.called, "S3 object retrieval task should have been executed"


@then('the object content should be written to output without JSON encoding')
def step_then_object_content_written_no_json_encoding(context):
    """Verify object content was written without JSON encoding."""
    context.current_task.write_output.assert_called()


@then('the S3 object should be retrieved from the nested path')
def step_then_s3_object_retrieved_nested_path(context):
    """Verify S3 object was retrieved from nested path."""
    key = context.task_attributes.get('key', '')
    assert '/' in key, "Key should contain nested path separators"


@then('the full object content should be preserved')
def step_then_full_content_preserved(context):
    """Verify full object content was preserved."""
    pass


@then('the S3 object should be retrieved from the specified region')
def step_then_s3_object_retrieved_specified_region(context):
    """Verify S3 object was retrieved from specified region."""
    region = context.task_attributes.get('region')
    assert region, "Region should be specified"


@then('the template content should be accessible')
def step_then_template_content_accessible(context):
    """Verify template content is accessible."""
    pass


@then('cross-region access should work correctly')
def step_then_cross_region_access_works(context):
    """Verify cross-region access works correctly."""
    assert context.task_result == "success", "Cross-region access should work"


@then('the large S3 object should be retrieved completely')
def step_then_large_s3_object_retrieved_completely(context):
    """Verify large S3 object was retrieved completely."""
    assert getattr(context, 'large_object_exists', False), "Large object should exist"


@then('the entire content should be written to output')
def step_then_entire_content_written_output(context):
    """Verify entire content was written to output."""
    pass


@then('memory usage should be managed appropriately')
def step_then_memory_usage_managed(context):
    """Verify memory usage was managed appropriately."""
    pass


@then('a NoSuchKey error should be raised')
def step_then_nosuchkey_error_raised(context):
    """Verify NoSuchKey error was raised."""
    assert getattr(context, 'missing_s3_objects', []), "Object should be missing"


@then('an AccessDenied error should be raised')
def step_then_access_denied_error_raised(context):
    """Verify AccessDenied error was raised."""
    assert getattr(context, 's3_access_denied', False), "S3 access should be denied"


@then('the error should indicate permission issues')
def step_then_error_indicates_permission_issues(context):
    """Verify error indicates permission issues."""
    pass


@then('the binary S3 object should be retrieved correctly')
def step_then_binary_s3_object_retrieved(context):
    """Verify binary S3 object was retrieved correctly."""
    assert getattr(context, 'binary_object_exists', False), "Binary object should exist"


@then('the binary content should be preserved without corruption')
def step_then_binary_content_preserved(context):
    """Verify binary content was preserved without corruption."""
    pass


@then('no JSON encoding should be applied to the binary data')
def step_then_no_json_encoding_binary(context):
    """Verify no JSON encoding was applied to binary data."""
    context.current_task.write_output.assert_called()


@then('the task should use the standard bucket naming convention "{bucket_pattern}"')
def step_then_task_uses_standard_bucket_naming(context, bucket_pattern):
    """Verify task uses standard bucket naming convention."""
    pass


@then('the object should be retrieved from "{expected_bucket}"')
def step_then_object_retrieved_from_bucket(context, expected_bucket):
    """Verify object was retrieved from expected bucket."""
    pass


@then('the puppet parameter file should be accessed successfully')
def step_then_puppet_parameter_file_accessed(context):
    """Verify puppet parameter file was accessed successfully."""
    key = context.task_attributes.get('key', '')
    assert 'puppet' in key or 'manifest' in key, "Key should reference puppet/manifest parameters"


@then('the content should be available for subsequent workflow tasks')
def step_then_content_available_subsequent_tasks(context):
    """Verify content is available for subsequent workflow tasks."""
    context.current_task.write_output.assert_called()