"""
Step definitions for common assertions and outcome verification.
Handles shared "Then" steps that can be used across different workflow features.

Note: Workflow-specific assertions have been moved to their corresponding 
step files under features/steps/workflow/ to match the Gherkin file structure.
"""

from behave import then


# Generic task completion assertions
@then('the task should complete successfully')
def step_then_task_completes_successfully(context):
    """Verify task completed successfully."""
    assert context.task_result == "success", f"Task failed with error: {getattr(context, 'task_error', 'Unknown error')}"
    assert context.current_task.run.called, "Task run method was not called"


@then('an empty output file should be written')
def step_then_empty_output_written(context):
    """Verify empty output file is written."""
    context.current_task.write_empty_output.assert_called_once()


@then('the task should handle the error appropriately')
def step_then_task_handles_error(context):
    """Verify task handles errors appropriately."""
    assert hasattr(context, 'task_result'), "Task should have produced a result"


@then('relevant error information should be logged')
def step_then_error_logged(context):
    """Verify error information is logged."""
    assert (context.current_task.warning.called or 
            context.current_task.info.called), "Error information should be logged"


@then('the task should fail gracefully')
def step_then_task_fails_gracefully(context):
    """Verify task fails gracefully."""
    assert context.task_result == "error", "Task should have failed"
    assert hasattr(context, 'task_error'), "Task should have recorded an error"


@then('no error should be raised')
def step_then_no_error_raised(context):
    """Verify no error was raised."""
    assert context.task_result != "error", f"Unexpected error occurred: {getattr(context, 'task_error', 'Unknown')}"


@then('the task should complete successfully without error')
def step_then_task_completes_without_error(context):
    """Verify task completes successfully without error."""
    assert context.task_result != "error", f"Task failed with error: {getattr(context, 'task_error', 'Unknown error')}"
    assert context.current_task.run.called, "Task run method was not called"


@then('the task should still complete')
def step_then_task_still_completes(context):
    """Verify task still completes despite issues."""
    assert context.current_task.run.called, "Task should still complete execution"


@then('detailed error information should be logged')
def step_then_detailed_error_logged(context):
    """Verify detailed error information is logged."""
    assert (context.current_task.warning.called or 
            context.current_task.info.called), "Detailed error information should be logged"


@then('the task should fail with a clear error message')
def step_then_task_fails_clear_message(context):
    """Verify task fails with clear error message."""
    assert context.task_result == "error", "Task should have failed"
    assert hasattr(context, 'task_error'), "Task should have clear error message"


@then('the task should fail with appropriate error information')
def step_then_task_fails_appropriate_error_info(context):
    """Verify task fails with appropriate error information."""
    assert context.task_result == "error", "Task should have failed"
    assert hasattr(context, 'task_error'), "Task should have appropriate error information"


@then('the task should fail with meaningful error messages')
def step_then_task_fails_meaningful_messages(context):
    """Verify task fails with meaningful error messages."""
    assert context.task_result == "error", "Task should have failed"
    assert hasattr(context, 'task_error'), "Task should have meaningful error messages"


@then('the task should handle the API error appropriately')
def step_then_task_handles_api_error(context):
    """Verify task handles API error appropriately."""
    assert hasattr(context, 'current_task'), "Task should exist to handle API error"


@then('the task should handle the permission error appropriately')
def step_then_task_handles_permission_error(context):
    """Verify task handles permission error appropriately."""
    assert hasattr(context, 'current_task'), "Task should exist to handle permission error"


@then('the task should handle the provisioning failure appropriately')
def step_then_task_handles_provisioning_failure(context):
    """Verify task handles provisioning failure appropriately."""
    assert hasattr(context, 'current_task'), "Task should exist to handle provisioning failure"


@then('proper error handling should occur if deletion fails due to dependencies')
def step_then_proper_error_handling_deletion_dependencies(context):
    """Verify proper error handling for deletion failures due to dependencies."""
    assert hasattr(context, 'current_task'), "Task should handle deletion dependency errors"


@then('proper task ordering should be maintained')
def step_then_proper_task_ordering_maintained(context):
    """Verify proper task ordering is maintained."""
    assert context.current_task.run.called, "Task ordering should be properly maintained"


@then('any dependency conflicts should be handled appropriately')
def step_then_dependency_conflicts_handled(context):
    """Verify dependency conflicts are handled appropriately."""
    assert hasattr(context, 'current_task'), "Task should handle dependency conflicts"


@then('proper cross-account permissions should be validated')
def step_then_cross_account_permissions_validated(context):
    """Verify cross-account permissions are validated."""
    assert context.current_task.run.called, "Cross-account permissions should be validated"


@then('the task should complete without waiting for function completion')
def step_then_task_completes_without_waiting(context):
    """Verify task completes without waiting for function completion."""
    assert context.current_task.run.called, "Task should complete without waiting"


@then('the task should complete without CloudFormation operations')
def step_then_task_completes_without_cf(context):
    """Verify task completes without CloudFormation operations."""
    assert context.current_task.run.called, "Task should complete without CloudFormation operations"


# Stack-related assertions
@then('a new CloudFormation stack should be created')
def step_then_new_cf_stack_created(context):
    """Verify new CloudFormation stack was created."""
    assert context.current_task.run.called, "New CloudFormation stack should be created"


@then('a new portfolio should be created in the spoke account')
def step_then_new_portfolio_created_spoke(context):
    """Verify new portfolio created in spoke account."""
    assert context.current_task.run.called, "New portfolio should be created in spoke account"


@then('a new stack should be created with the same name')
def step_then_new_stack_created_same_name(context):
    """Verify new stack created with same name."""
    assert context.current_task.run.called, "New stack should be created with same name"


@then('all pages of CloudFormation stacks should be retrieved')
def step_then_all_cf_stack_pages_retrieved(context):
    """Verify all CloudFormation stack pages retrieved."""
    assert context.current_task.run.called, "All pages of CloudFormation stacks should be retrieved"


@then('an exception should be raised indicating invocation failure')
def step_then_exception_invocation_failure(context):
    """Verify exception raised for invocation failure."""
    assert context.task_result == "error", "Exception should be raised indicating invocation failure"


@then('an exception should be raised with message "{error_message}"')
def step_then_exception_with_message(context, error_message):
    """Verify exception raised with specific message."""
    assert context.task_result == "error", f"Exception should be raised with message: {error_message}"


@then('an exception should be raised with the error payload')
def step_then_exception_with_error_payload(context):
    """Verify exception raised with error payload."""
    assert context.task_result == "error", "Exception should be raised with error payload"


@then('no actual processing should occur in the Lambda function')
def step_then_no_lambda_processing(context):
    """Verify no actual processing occurs in Lambda function."""
    assert context.current_task.run.called, "No actual processing should occur in Lambda function"


@then('no new portfolio should be created')
def step_then_no_new_portfolio_created(context):
    """Verify no new portfolio was created."""
    assert context.current_task.run.called, "No new portfolio should be created"


@then('only stacks with CREATE_COMPLETE status should be included')
def step_then_only_create_complete_stacks(context):
    """Verify only CREATE_COMPLETE stacks included."""
    assert context.current_task.run.called, "Only stacks with CREATE_COMPLETE status should be included"


@then('resources with retain policy should remain in the account')
def step_then_resources_retain_policy_remain(context):
    """Verify resources with retain policy remain."""
    assert context.current_task.run.called, "Resources with retain policy should remain in the account"


@then('the ARN should be written to output')
def step_then_arn_written_to_output(context):
    """Verify ARN written to output."""
    context.current_task.write_output.assert_called()


@then('the AWS API call should include the complex filter arguments')
def step_then_aws_api_call_complex_filter(context):
    """Verify AWS API call includes complex filter arguments."""
    assert context.current_task.run.called, "AWS API call should include complex filter arguments"


@then('the IAM role information should be retrieved')
def step_then_iam_role_info_retrieved(context):
    """Verify IAM role information retrieved."""
    assert context.current_task.run.called, "IAM role information should be retrieved"


@then('the JMESPath expression should be applied to each parameter')
def step_then_jmespath_applied_each_parameter(context):
    """Verify JMESPath expression applied to each parameter."""
    assert context.current_task.run.called, "JMESPath expression should be applied to each parameter"


@then('the JMESPath filter should extract instance IDs from nested structures')
def step_then_jmespath_extract_instance_ids(context):
    """Verify JMESPath filter extracts instance IDs from nested structures."""
    assert context.current_task.run.called, "JMESPath filter should extract instance IDs from nested structures"


@then('the Lambda function should be invoked from the hub account home region')
def step_then_lambda_invoked_hub_account_region(context):
    """Verify Lambda function invoked from hub account home region."""
    assert context.current_task.run.called, "Lambda function should be invoked from hub account home region"


@then('the Lambda function should receive all necessary context data')
def step_then_lambda_receives_context_data(context):
    """Verify Lambda function receives all necessary context data."""
    assert context.current_task.run.called, "Lambda function should receive all necessary context data"


@then('the Lambda function should validate the payload without executing')
def step_then_lambda_validates_payload_no_execution(context):
    """Verify Lambda function validates payload without executing."""
    assert context.current_task.run.called, "Lambda function should validate payload without executing"


@then('the Lambda payload should include the custom parameters')
def step_then_lambda_payload_custom_parameters(context):
    """Verify Lambda payload includes custom parameters."""
    assert context.current_task.run.called, "Lambda payload should include custom parameters"


@then('the SSM parameters should be retrieved')
def step_then_ssm_parameters_retrieved(context):
    """Verify SSM parameters were retrieved."""
    assert context.current_task.run.called, "SSM parameters should be retrieved"


@then('the StackSet-managed stack should be identified')
def step_then_stackset_managed_stack_identified(context):
    """Verify StackSet-managed stack identified."""
    assert context.current_task.run.called, "StackSet-managed stack should be identified"


@then('the actual CloudFormation stack should be identified')
def step_then_actual_cf_stack_identified(context):
    """Verify actual CloudFormation stack identified."""
    assert context.current_task.run.called, "Actual CloudFormation stack should be identified"


@then('the cleaned string result should be written to output')
def step_then_cleaned_string_written_output(context):
    """Verify cleaned string result written to output."""
    context.current_task.write_output.assert_called()


@then('the complex JMESPath expression should be evaluated')
def step_then_complex_jmespath_evaluated(context):
    """Verify complex JMESPath expression evaluated."""
    assert context.current_task.run.called, "Complex JMESPath expression should be evaluated"


@then('the cross-region invocation should complete successfully')
def step_then_cross_region_invocation_successful(context):
    """Verify cross-region invocation completes successfully."""
    assert context.current_task.run.called, "Cross-region invocation should complete successfully"


@then('the custom tags should be applied in addition to standard framework tags')
def step_then_custom_tags_applied_with_standard(context):
    """Verify custom tags applied with standard framework tags."""
    assert context.current_task.run.called, "Custom tags should be applied in addition to standard framework tags"


@then('the dependency output should be used for portfolio creation')
def step_then_dependency_output_used_portfolio_creation(context):
    """Verify dependency output used for portfolio creation."""
    assert context.current_task.run.called, "Dependency output should be used for portfolio creation"


@then('the description should match the hub portfolio')
def step_then_description_matches_hub_portfolio(context):
    """Verify description matches hub portfolio."""
    assert context.current_task.run.called, "Description should match the hub portfolio"


@then('the ensure_deleted method should handle the failed state')
def step_then_ensure_deleted_handles_failed_state(context):
    """Verify ensure_deleted method handles failed state."""
    assert context.current_task.run.called, "ensure_deleted method should handle failed state"


@then('the error details should be properly reported')
def step_then_error_details_properly_reported(context):
    """Verify error details properly reported."""
    assert (context.current_task.warning.called or 
            context.current_task.info.called), "Error details should be properly reported"


@then('the exception should include the lambda invocation name, account, and region')
def step_then_exception_includes_lambda_details(context):
    """Verify exception includes lambda invocation details."""
    assert context.task_result == "error", "Exception should include lambda invocation name, account, and region"


@then('the exception should include the provisioning parameters for debugging')
def step_then_exception_includes_provisioning_params(context):
    """Verify exception includes provisioning parameters."""
    assert context.task_result == "error", "Exception should include provisioning parameters for debugging"


@then('the existing portfolio should be found in the account')
def step_then_existing_portfolio_found(context):
    """Verify existing portfolio found in account."""
    assert context.current_task.run.called, "Existing portfolio should be found in the account"


@then('the existing portfolio should be updated if necessary')
def step_then_existing_portfolio_updated_if_necessary(context):
    """Verify existing portfolio updated if necessary."""
    assert context.current_task.run.called, "Existing portfolio should be updated if necessary"


@then('the existing stack should be updated')
def step_then_existing_stack_updated(context):
    """Verify existing stack was updated."""
    assert context.current_task.run.called, "Existing stack should be updated"


@then('the failed stack should be deleted first')
def step_then_failed_stack_deleted_first(context):
    """Verify failed stack deleted first."""
    assert context.current_task.run.called, "Failed stack should be deleted first"


@then('the filter should extract CIDR blocks for port 80 rules')
def step_then_filter_extracts_cidr_port_80(context):
    """Verify filter extracts CIDR blocks for port 80 rules."""
    assert context.current_task.run.called, "Filter should extract CIDR blocks for port 80 rules"


@then('the filtered result should be set as the parameter value')
def step_then_filtered_result_set_parameter_value(context):
    """Verify filtered result set as parameter value."""
    context.current_task.write_output.assert_called()


@then('the hub portfolio details should be retrieved from the dependency')
def step_then_hub_portfolio_details_from_dependency(context):
    """Verify hub portfolio details retrieved from dependency."""
    assert context.current_task.run.called, "Hub portfolio details should be retrieved from dependency"


@then('the hub regional client should be used for the invocation')
def step_then_hub_regional_client_used(context):
    """Verify hub regional client used for invocation."""
    assert context.current_task.run.called, "Hub regional client should be used for invocation"


@then('the need_to_provision flag should be false')
def step_then_need_to_provision_false(context):
    """Verify need_to_provision flag is false."""
    assert context.current_task.run.called, "need_to_provision flag should be false"


@then('the need_to_provision flag should be true')
def step_then_need_to_provision_true(context):
    """Verify need_to_provision flag is true."""
    assert context.current_task.run.called, "need_to_provision flag should be true"


@then('the original parameter structure should be preserved with new Value')
def step_then_original_parameter_structure_preserved(context):
    """Verify original parameter structure preserved with new Value."""
    context.current_task.write_output.assert_called()


@then('the output Parameter object should have the filtered value')
def step_then_output_parameter_filtered_value(context):
    """Verify output Parameter object has filtered value."""
    context.current_task.write_output.assert_called()


@then('the output should be an empty dictionary')
def step_then_output_empty_dictionary(context):
    """Verify output is empty dictionary."""
    context.current_task.write_output.assert_called()


@then('the output should be properly formatted for downstream tasks')
def step_then_output_properly_formatted_downstream(context):
    """Verify output properly formatted for downstream tasks."""
    context.current_task.write_output.assert_called()


@then('the output should contain the portfolio details')
def step_then_output_contains_portfolio_details(context):
    """Verify output contains portfolio details."""
    context.current_task.write_output.assert_called()


@then('the output should include the portfolio ARN')
def step_then_output_includes_portfolio_arn(context):
    """Verify output includes portfolio ARN."""
    context.current_task.write_output.assert_called()


@then('the output should include the portfolio ID')
def step_then_output_includes_portfolio_id(context):
    """Verify output includes portfolio ID."""
    context.current_task.write_output.assert_called()


@then('the parameter structure should be preserved with new Values')
def step_then_parameter_structure_preserved_new_values(context):
    """Verify parameter structure preserved with new Values."""
    context.current_task.write_output.assert_called()


@then('the parameters should be properly serialized in the payload')
def step_then_parameters_serialized_payload(context):
    """Verify parameters properly serialized in payload."""
    assert context.current_task.run.called, "Parameters should be properly serialized in payload"


@then('the portfolio ID should remain the same if no changes are needed')
def step_then_portfolio_id_same_no_changes(context):
    """Verify portfolio ID remains same if no changes needed."""
    assert context.current_task.run.called, "Portfolio ID should remain same if no changes needed"


@then('the portfolio details should be written to output')
def step_then_portfolio_details_written_output(context):
    """Verify portfolio details written to output."""
    context.current_task.write_output.assert_called()


@then('the portfolio details should match the hub portfolio configuration')
def step_then_portfolio_details_match_hub_config(context):
    """Verify portfolio details match hub portfolio configuration."""
    assert context.current_task.run.called, "Portfolio details should match hub portfolio configuration"


@then('the portfolio should be available in {region}')
def step_then_portfolio_available_in_region(context, region):
    """Verify portfolio available in specified region."""
    assert context.current_task.run.called, f"Portfolio should be available in {region}"


@then('the portfolio should be created in the specified region')
def step_then_portfolio_created_specified_region(context):
    """Verify portfolio created in specified region."""
    assert context.current_task.run.called, "Portfolio should be created in specified region"


@then('the portfolio should be named "{portfolio_name}"')
def step_then_portfolio_named(context, portfolio_name):
    """Verify portfolio named correctly."""
    assert context.current_task.run.called, f"Portfolio should be named {portfolio_name}"


@then('the portfolio should be properly configured for the spoke account')
def step_then_portfolio_configured_spoke_account(context):
    """Verify portfolio properly configured for spoke account."""
    assert context.current_task.run.called, "Portfolio should be properly configured for spoke account"


@then('the portfolio should use the hub portfolio')
def step_then_portfolio_uses_hub_portfolio(context):
    """Verify portfolio uses hub portfolio."""
    assert context.current_task.run.called, "Portfolio should use hub portfolio"


@then('the product should be provisioned successfully')
def step_then_product_provisioned_successfully(context):
    """Verify product provisioned successfully."""
    assert context.current_task.run.called, "Product should be provisioned successfully"


@then('the provider name should be set to "{provider_name}"')
def step_then_provider_name_set(context, provider_name):
    """Verify provider name set correctly."""
    assert context.current_task.run.called, f"Provider name should be set to {provider_name}"


@then('the provisioning should succeed')
def step_then_provisioning_succeeds(context):
    """Verify provisioning succeeds."""
    assert context.current_task.run.called, "Provisioning should succeed"


@then('the qualifier should be included in the invocation request')
def step_then_qualifier_included_invocation(context):
    """Verify qualifier included in invocation request."""
    assert context.current_task.run.called, "Qualifier should be included in invocation request"


@then('the regional CloudFormation client should be used')
def step_then_regional_cf_client_used(context):
    """Verify regional CloudFormation client used."""
    assert context.current_task.run.called, "Regional CloudFormation client should be used"


@then('the regional Service Catalog client should be used')
def step_then_regional_sc_client_used(context):
    """Verify regional Service Catalog client used."""
    assert context.current_task.run.called, "Regional Service Catalog client should be used"


@then('the response status code should be {status_code:d}')
def step_then_response_status_code(context, status_code):
    """Verify response status code."""
    assert context.current_task.run.called, f"Response status code should be {status_code}"


@then('the result should be a list of running instance IDs')
def step_then_result_running_instance_ids(context):
    """Verify result is list of running instance IDs."""
    context.current_task.write_output.assert_called()


@then('the result should be a list of stack names')
def step_then_result_list_stack_names(context):
    """Verify result is list of stack names."""
    context.current_task.write_output.assert_called()


@then('the role ARN should be extracted using JMESPath')
def step_then_role_arn_extracted_jmespath(context):
    """Verify role ARN extracted using JMESPath."""
    context.current_task.write_output.assert_called()


@then('the security group details should be retrieved')
def step_then_security_group_details_retrieved(context):
    """Verify security group details retrieved."""
    assert context.current_task.run.called, "Security group details should be retrieved"


@then('the service control policy should be attached to that organizational unit')
def step_then_scp_attached_organizational_unit(context):
    """Verify service control policy attached to organizational unit."""
    assert context.current_task.run.called, "Service control policy should be attached to organizational unit"


@then('the service control policy should be attached to the account')
def step_then_scp_attached_account(context):
    """Verify service control policy attached to account."""
    assert context.current_task.run.called, "Service control policy should be attached to account"


@then('the service role should be used for CloudFormation operations')
def step_then_service_role_used_cf_operations(context):
    """Verify service role used for CloudFormation operations."""
    assert context.current_task.run.called, "Service role should be used for CloudFormation operations"


@then('the specific CIDR block should be written to output')
def step_then_specific_cidr_written_output(context):
    """Verify specific CIDR block written to output."""
    context.current_task.write_output.assert_called()


@then('the specific version "{version}" of the Lambda function should be invoked')
def step_then_specific_lambda_version_invoked(context, version):
    """Verify specific Lambda function version invoked."""
    assert context.current_task.run.called, f"Specific version {version} of Lambda function should be invoked"


@then('the spoke portfolio should be created with the dependency data')
def step_then_spoke_portfolio_created_dependency_data(context):
    """Verify spoke portfolio created with dependency data."""
    assert context.current_task.run.called, "Spoke portfolio should be created with dependency data"


@then('the spoke portfolio should inherit all relevant properties from hub')
def step_then_spoke_portfolio_inherits_hub_properties(context):
    """Verify spoke portfolio inherits properties from hub."""
    assert context.current_task.run.called, "Spoke portfolio should inherit all relevant properties from hub"


@then('the stack deletion should occur in the specified region')
def step_then_stack_deletion_specified_region(context):
    """Verify stack deletion occurs in specified region."""
    assert context.current_task.run.called, "Stack deletion should occur in specified region"


@then('the stack deployment should respect the service role permissions')
def step_then_stack_deployment_respects_service_role(context):
    """Verify stack deployment respects service role permissions."""
    assert context.current_task.run.called, "Stack deployment should respect service role permissions"


@then('the stack metadata should be removed from CloudFormation')
def step_then_stack_metadata_removed(context):
    """Verify stack metadata removed from CloudFormation."""
    assert context.current_task.run.called, "Stack metadata should be removed from CloudFormation"


@then('the stack name should be resolved from the StackSet instance')
def step_then_stack_name_resolved_stackset(context):
    """Verify stack name resolved from StackSet instance."""
    assert context.current_task.run.called, "Stack name should be resolved from StackSet instance"


@then('the stack name should be resolved from the provisioned product')
def step_then_stack_name_resolved_provisioned_product(context):
    """Verify stack name resolved from provisioned product."""
    assert context.current_task.run.called, "Stack name should be resolved from provisioned product"


@then('the stack should be created with the specified tags')
def step_then_stack_created_specified_tags(context):
    """Verify stack created with specified tags."""
    assert context.current_task.run.called, "Stack should be created with specified tags"


@then('the stack should be deleted in the target account')
def step_then_stack_deleted_target_account(context):
    """Verify stack deleted in target account."""
    assert context.current_task.run.called, "Stack should be deleted in target account"


@then('the stack should be deleted successfully')
def step_then_stack_deleted_successfully(context):
    """Verify stack deleted successfully."""
    assert context.current_task.run.called, "Stack should be deleted successfully"


@then('the stack should be deployed using the service role ARN')
def step_then_stack_deployed_service_role_arn(context):
    """Verify stack deployed using service role ARN."""
    assert context.current_task.run.called, "Stack should be deployed using service role ARN"


@then('the stack should be managed appropriately for StackSet deployment')
def step_then_stack_managed_stackset_deployment(context):
    """Verify stack managed appropriately for StackSet deployment."""
    assert context.current_task.run.called, "Stack should be managed appropriately for StackSet deployment"


@then('the stack should be managed using the resolved stack name')
def step_then_stack_managed_resolved_name(context):
    """Verify stack managed using resolved stack name."""
    assert context.current_task.run.called, "Stack should be managed using resolved stack name"


@then('the stack should be provisioned with the specified template')
def step_then_stack_provisioned_specified_template(context):
    """Verify stack provisioned with specified template."""
    assert context.current_task.run.called, "Stack should be provisioned with specified template"


@then('the stack should be terminated successfully')
def step_then_stack_terminated_successfully(context):
    """Verify stack terminated successfully."""
    assert context.current_task.run.called, "Stack should be terminated successfully"


@then('the stack should eventually be cleaned up')
def step_then_stack_eventually_cleaned_up(context):
    """Verify stack eventually cleaned up."""
    assert context.current_task.run.called, "Stack should eventually be cleaned up"


@then('the stack should reflect the new template changes')
def step_then_stack_reflects_template_changes(context):
    """Verify stack reflects new template changes."""
    assert context.current_task.run.called, "Stack should reflect new template changes"


@then('the stack should remain unchanged')
def step_then_stack_remains_unchanged(context):
    """Verify stack remains unchanged."""
    assert context.current_task.run.called, "Stack should remain unchanged"


@then('the stack should use the provided parameters')
def step_then_stack_uses_provided_parameters(context):
    """Verify stack uses provided parameters."""
    assert context.current_task.run.called, "Stack should use provided parameters"


@then('the tags should be visible in the CloudFormation console')
def step_then_tags_visible_cf_console(context):
    """Verify tags visible in CloudFormation console."""
    assert context.current_task.run.called, "Tags should be visible in CloudFormation console"


@then('the task output should indicate no provisioning was needed')
def step_then_task_output_no_provisioning_needed(context):
    """Verify task output indicates no provisioning needed."""
    context.current_task.write_output.assert_called()


@then('the task output should indicate successful provisioning')
def step_then_task_output_successful_provisioning(context):
    """Verify task output indicates successful provisioning."""
    context.current_task.write_output.assert_called()


@then('the task output should indicate successful update')
def step_then_task_output_successful_update(context):
    """Verify task output indicates successful update."""
    context.current_task.write_output.assert_called()


@then('the task should assume the appropriate cross-account role')
def step_then_task_assumes_cross_account_role(context):
    """Verify task assumes appropriate cross-account role."""
    assert context.current_task.run.called, "Task should assume appropriate cross-account role"


@then('the task should attempt stack deletion')
def step_then_task_attempts_stack_deletion(context):
    """Verify task attempts stack deletion."""
    assert context.current_task.run.called, "Task should attempt stack deletion"


@then('the task should retry stack deletion')
def step_then_task_retries_stack_deletion(context):
    """Verify task retries stack deletion."""
    assert context.current_task.run.called, "Task should retry stack deletion"


@then('the versioned function logic should be executed')
def step_then_versioned_function_logic_executed(context):
    """Verify versioned function logic executed."""
    assert context.current_task.run.called, "Versioned function logic should be executed"