"""
Step definitions for creating and configuring task parameters in Gherkin tests.
Handles parameter setup steps that are shared across different task types.

Note: Task creation steps have been moved to workflow-specific step files 
under features/steps/workflow/ to match the Gherkin file structure.
"""

from behave import given
from features.steps.common_steps import parse_table_to_dict, parse_table_to_list_of_dicts


# Additional parameter setup steps
@given('launch parameters:')
def step_given_launch_parameters(context):
    """Set up launch parameters from table."""
    # Parse table with parameter_name/parameter_value columns
    parameters = {row['parameter_name']: row['parameter_value'] for row in context.table}
    context.launch_parameters = parameters
    if hasattr(context.current_task, 'launch_parameters'):
        context.current_task.launch_parameters = parameters


@given('manifest parameters:')
def step_given_manifest_parameters(context):
    """Set up manifest parameters from table."""
    # Parse table with parameter_name/parameter_value columns
    parameters = {row['parameter_name']: row['parameter_value'] for row in context.table}
    context.manifest_parameters = parameters
    if hasattr(context.current_task, 'manifest_parameters'):
        context.current_task.manifest_parameters = parameters


@given('account parameters:')
def step_given_account_parameters(context):
    """Set up account parameters from table."""
    # Parse table with parameter_name/parameter_value columns
    parameters = {row['parameter_name']: row['parameter_value'] for row in context.table}
    context.account_parameters = parameters
    if hasattr(context.current_task, 'account_parameters'):
        context.current_task.account_parameters = parameters


@given('SSM parameter inputs:')
def step_given_ssm_parameter_inputs(context):
    """Set up SSM parameter inputs from table."""
    ssm_params = [row['ssm_param_name'] for row in context.table]
    context.ssm_param_inputs = ssm_params
    if hasattr(context.current_task, 'ssm_param_inputs'):
        context.current_task.ssm_param_inputs = ssm_params


@given('tags:')
def step_given_tags(context):
    """Set up tags from table."""
    # Tags use tag_key/tag_value columns
    tags = [{'tag_key': row['tag_key'], 'tag_value': row['tag_value']} for row in context.table]
    context.tags = tags
    if hasattr(context.current_task, 'tags'):
        context.current_task.tags = tags


@given('capabilities:')
def step_given_capabilities(context):
    """Set up capabilities from table."""
    capabilities = [row['capability'] for row in context.table]
    context.capabilities = capabilities
    if hasattr(context.current_task, 'capabilities'):
        context.current_task.capabilities = capabilities


@given('content:')
def step_given_content(context):
    """Set up content from table."""
    # Content uses policy_section/policy_value columns
    content = {row['policy_section']: row['policy_value'] for row in context.table}
    context.content = content
    if hasattr(context.current_task, 'content'):
        context.current_task.content = content


@given('complex content with multiple statements and conditions')
def step_given_complex_content(context):
    """Set up complex policy content."""
    complex_content = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "Action": "*",
                "Resource": "*",
                "Condition": {
                    "StringNotEquals": {
                        "aws:RequestedRegion": ["us-east-1", "us-west-2"]
                    }
                }
            }
        ]
    }
    context.content = complex_content
    if hasattr(context.current_task, 'content'):
        context.current_task.content = complex_content
