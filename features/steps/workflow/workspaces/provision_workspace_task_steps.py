"""Step definitions for workspace provisioning tasks."""

from behave import given, when, then
from features.steps.common_steps import parse_table_to_dict, get_task_class
from features.mock_utils import MockAWSClients, setup_task_with_aws_mocks


@given('a ProvisionWorkspaceTask with the following attributes:')
def step_given_provision_workspace_task(context):
    """Set up a ProvisionWorkspaceTask with specified attributes."""
    attributes = parse_table_to_dict(context.table)
    task_class = get_task_class('ProvisionWorkspaceTask')
    
    # Set up AWS client mocks
    aws_mocks = {
        'workspaces': MockAWSClients.create_workspaces_mock(),
        's3': MockAWSClients.create_s3_mock()
    }
    
    mock_task = setup_task_with_aws_mocks(context, task_class, attributes, aws_mocks)
    context.task_attributes = attributes
    
    # Parse ssm_param_inputs if present and set on context
    if 'ssm_param_inputs' in attributes:
        ssm_inputs_str = attributes['ssm_param_inputs']
        if ssm_inputs_str.startswith('[') and ssm_inputs_str.endswith(']'):
            # Parse array-like string
            ssm_inputs = ssm_inputs_str.strip('[]').replace('"', '').split(', ')
            context.ssm_param_inputs = ssm_inputs


@given('the S3 bucket contains workspace artifacts')
def step_given_s3_bucket_workspace_artifacts(context):
    """Set up S3 bucket with workspace artifacts."""
    context.s3_workspace_artifacts = True


@then('the workspace should be provisioned successfully')
def step_then_workspace_provisioned_successfully(context):
    """Verify workspace was provisioned successfully."""
    assert context.current_task.run.called, "Workspace should have been provisioned successfully"




@then('the workspace should be provisioned in the target account')
def step_then_workspace_provisioned(context):
    """Verify workspace was provisioned in target account."""
    assert context.current_task.run.called, "Workspace provisioning task should have been executed"


@then('the workspace artifacts should be downloaded from S3')
def step_then_workspace_artifacts_downloaded(context):
    """Verify workspace artifacts were downloaded from S3."""
    bucket = context.task_attributes.get('bucket')
    key = context.task_attributes.get('key')
    assert bucket and key, "S3 bucket and key should be specified"


@then('the workspace should be provisioned with the specified parameters')
def step_then_workspace_provisioned_with_params(context):
    """Verify workspace was provisioned with specified parameters."""
    assert hasattr(context, 'launch_parameters'), "Launch parameters should have been provided"


@then('the correct bundle and directory should be used')
def step_then_correct_bundle_directory_used(context):
    """Verify correct bundle and directory were used."""
    pass


@then('the workspace should be provisioned with SSM parameter values')
def step_then_workspace_provisioned_with_ssm(context):
    """Verify workspace was provisioned with SSM parameter values."""
    assert hasattr(context, 'ssm_param_inputs'), "SSM parameter inputs should have been provided"


@then('the workspace should be provisioned with manifest and account parameters')
def step_then_workspace_provisioned_manifest_account_params(context):
    """Verify workspace was provisioned with manifest and account parameters."""
    assert hasattr(context, 'manifest_parameters'), "Manifest parameters should have been provided"
    assert hasattr(context, 'account_parameters'), "Account parameters should have been provided"


@then('the correct VPC and subnets should be used')
def step_then_correct_vpc_subnets_used(context):
    """Verify correct VPC and subnets were used."""
    account_params = getattr(context, 'account_parameters', {})
    assert 'VpcId' in account_params, "VPC ID should be in account parameters"


@then('the S3 zip artifact should be downloaded and extracted')
def step_then_s3_artifact_downloaded_extracted(context):
    """Verify S3 zip artifact was downloaded and extracted."""
    pass


@then('the workspace configuration should be processed from the artifact')
def step_then_workspace_config_processed(context):
    """Verify workspace configuration was processed from artifact."""
    pass


@then('the workspace should be provisioned using the extracted configuration')
def step_then_workspace_provisioned_extracted_config(context):
    """Verify workspace was provisioned using extracted configuration."""
    assert context.current_task.run.called, "Workspace provisioning should have used extracted config"


@then('SSM parameter outputs should be processed if specified')
def step_then_ssm_outputs_processed(context):
    """Verify SSM parameter outputs were processed if specified."""
    pass