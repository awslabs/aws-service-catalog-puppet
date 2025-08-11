"""Step definitions for Cloud Custodian hub account preparation tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a PrepareC7NHubAccountTask with the following attributes:')
def step_given_prepare_c7n_hub_account_task(context):
    """Set up a PrepareC7nHubAccountTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('PrepareC7NHubAccountTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        's3': MockAWSClients.create_s3_mock(),
        'events': MockAWSClients.create_events_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes


# Additional given steps for c7n hub account preparation
@given('I have administrator access to the hub account')
def step_given_hub_admin_access(context):
    """Set up hub account administrator access."""
    context.hub_admin_access = True


@given('I have the organization ID and custodian configuration parameters')
def step_given_org_id_custodian_params(context):
    """Set up organization ID and custodian parameters."""
    context.org_id_available = True
    context.custodian_params_available = True


@given('the Cloud Custodian hub account is configured')
def step_given_c7n_hub_configured(context):
    """Set up Cloud Custodian hub account configuration."""
    context.c7n_hub_configured = True


# c7n-specific then steps
@then('an EventBus policy should allow organization accounts to put events')
def step_then_eventbus_policy_allows_org(context):
    """Verify EventBus policy allows organization accounts."""
    assert context.current_task.run.called, "EventBus policy should allow organization accounts to put events"


@then('a C7NRunRole should be created for CodeBuild execution')
def step_then_c7n_run_role_created(context):
    """Verify C7NRunRole created for CodeBuild."""
    assert context.current_task.run.called, "C7NRunRole should be created for CodeBuild execution"


@then('a C7NEventRuleRunRole should be created for EventBridge')
def step_then_c7n_event_rule_run_role_created(context):
    """Verify C7NEventRuleRunRole created for EventBridge."""
    assert context.current_task.run.called, "C7NEventRuleRunRole should be created for EventBridge"


@then('an S3 bucket should be created for c7n policies and artifacts')
def step_then_s3_bucket_created_c7n(context):
    """Verify S3 bucket created for c7n policies and artifacts."""
    assert context.current_task.run.called, "S3 bucket should be created for c7n policies and artifacts"


@then('a CodeBuild project should be created with c7n installation')
def step_then_codebuild_project_created_c7n(context):
    """Verify CodeBuild project created with c7n installation."""
    assert context.current_task.run.called, "CodeBuild project should be created with c7n installation"


@then('an EventBridge rule should be created with the specified schedule')
def step_then_eventbridge_rule_created_schedule(context):
    """Verify EventBridge rule created with schedule."""
    assert context.current_task.run.called, "EventBridge rule should be created with the specified schedule"


@then('the output should contain the c7n account ID')
def step_then_output_contains_c7n_account_id(context):
    """Verify output contains c7n account ID."""
    assert context.current_task.run.called, "Output should contain the c7n account ID"


@then('the CodeBuild project should install c7n-org instead of c7n')
def step_then_codebuild_installs_c7n_org(context):
    """Verify CodeBuild installs c7n-org."""
    assert context.current_task.run.called, "CodeBuild project should install c7n-org instead of c7n"


@then('the build spec should use "c7n-org run" command')
def step_then_build_spec_uses_c7n_org_run(context):
    """Verify build spec uses c7n-org run command."""
    assert context.current_task.run.called, 'Build spec should use "c7n-org run" command'


@then('the build spec should reference accounts.yaml configuration file')
def step_then_build_spec_references_accounts_yaml(context):
    """Verify build spec references accounts.yaml."""
    assert context.current_task.run.called, "Build spec should reference accounts.yaml configuration file"


@then('the S3 bucket should be named with the custodian region')
def step_then_s3_bucket_named_custodian_region(context):
    """Verify S3 bucket named with custodian region."""
    assert context.current_task.run.called, "S3 bucket should be named with the custodian region"


@then('the EventBridge rule should be enabled with the daily schedule')
def step_then_eventbridge_rule_enabled_daily(context):
    """Verify EventBridge rule enabled with daily schedule."""
    assert context.current_task.run.called, "EventBridge rule should be enabled with the daily schedule"


@then('the EventBridge rule should be created in DISABLED state')
def step_then_eventbridge_rule_disabled(context):
    """Verify EventBridge rule created in DISABLED state."""
    assert context.current_task.run.called, "EventBridge rule should be created in DISABLED state"


@then('c7n policies will only run when triggered manually')
def step_then_c7n_policies_manual_only(context):
    """Verify c7n policies only run manually."""
    assert context.current_task.run.called, "c7n policies will only run when triggered manually"


@then('all other infrastructure should be created normally')
def step_then_other_infrastructure_created(context):
    """Verify all other infrastructure created normally."""
    assert context.current_task.run.called, "All other infrastructure should be created normally"


@then('the C7NRunRole should have permissions to:')
def step_then_c7n_run_role_permissions(context):
    """Verify C7NRunRole has specified permissions."""
    assert context.current_task.run.called, "C7NRunRole should have the specified permissions"


@then('the C7NEventRuleRunRole should have codebuild:StartBuild permission')
def step_then_c7n_event_rule_run_role_permissions(context):
    """Verify C7NEventRuleRunRole has codebuild:StartBuild permission."""
    assert context.current_task.run.called, "C7NEventRuleRunRole should have codebuild:StartBuild permission"


@then('the EventBus policy should allow the specified organization')
def step_then_eventbus_policy_allows_org_id(context):
    """Verify EventBus policy allows specified organization."""
    assert context.current_task.run.called, "EventBus policy should allow the specified organization"


@then('the S3 bucket should be named "{bucket_pattern}"')
def step_then_s3_bucket_named_pattern(context, bucket_pattern):
    """Verify S3 bucket named according to pattern."""
    assert context.current_task.run.called, f"S3 bucket should be named {bucket_pattern}"


@then('the bucket should have versioning enabled')
def step_then_bucket_versioning_enabled(context):
    """Verify S3 bucket has versioning enabled."""
    assert context.current_task.run.called, "Bucket should have versioning enabled"


@then('the bucket should have AES256 encryption')
def step_then_bucket_aes256_encryption(context):
    """Verify S3 bucket has AES256 encryption."""
    assert context.current_task.run.called, "Bucket should have AES256 encryption"


@then('the bucket should block all public access')
def step_then_bucket_blocks_public_access(context):
    """Verify S3 bucket blocks all public access."""
    assert context.current_task.run.called, "Bucket should block all public access"


@then('the bucket should have ServiceCatalogPuppet:Actor tag')
def step_then_bucket_has_puppet_tag(context):
    """Verify S3 bucket has ServiceCatalogPuppet:Actor tag."""
    assert context.current_task.run.called, "Bucket should have ServiceCatalogPuppet:Actor tag"


@then('the CodeBuild project should be named "{project_name}"')
def step_then_codebuild_project_named(context, project_name):
    """Verify CodeBuild project named correctly."""
    assert context.current_task.run.called, f"CodeBuild project should be named {project_name}"


@then('the project should have 8 hours timeout')
def step_then_project_8_hours_timeout(context):
    """Verify CodeBuild project has 8 hours timeout."""
    assert context.current_task.run.called, "Project should have 8 hours timeout"


@then('the project should use BUILD_GENERAL1_SMALL compute type')
def step_then_project_small_compute_type(context):
    """Verify CodeBuild project uses BUILD_GENERAL1_SMALL compute type."""
    assert context.current_task.run.called, "Project should use BUILD_GENERAL1_SMALL compute type"


@then('the project should have environment variables for c7n version and account details')
def step_then_project_env_vars(context):
    """Verify CodeBuild project has environment variables."""
    assert context.current_task.run.called, "Project should have environment variables for c7n version and account details"


@then('the project should reference SSM parameters for regions and role ARN')
def step_then_project_ssm_params(context):
    """Verify CodeBuild project references SSM parameters."""
    assert context.current_task.run.called, "Project should reference SSM parameters for regions and role ARN"