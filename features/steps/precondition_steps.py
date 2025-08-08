"""
Step definitions for handling preconditions and test setup.
Manages the state of AWS resources and dependencies before task execution.
"""

from behave import given
from unittest.mock import MagicMock
from features.mock_utils import CommonTestData


@given('no previous provisioned product exists')
def step_given_no_previous_provisioned_product(context):
    """Set up condition where no provisioned product exists."""
    # Configure ServiceCatalog mock to raise ResourceNotFoundException
    context.mock_service_catalog.describe_provisioned_product.side_effect = Exception("ResourceNotFoundException")
    context.product_previously_provisioned = False


@given('a provisioned product exists with the specified launch name')
def step_given_provisioned_product_exists(context):
    """Set up condition where a provisioned product exists."""
    context.mock_service_catalog.describe_provisioned_product.return_value = {
        'ProvisionedProductDetail': {
            'Id': 'pp-existing123',
            'Name': context.task_attributes.get('launch_name', 'test-launch'),
            'Status': 'AVAILABLE',
            'ProductId': 'prod-test123',
            'ProvisioningArtifactId': 'pa-test123'
        }
    }
    context.product_previously_provisioned = True


@given('no provisioned product exists with the specified launch name')
def step_given_no_provisioned_product_exists(context):
    """Set up condition where no provisioned product exists with the name."""
    context.mock_service_catalog.describe_provisioned_product.side_effect = Exception("ResourceNotFoundException")
    context.product_previously_provisioned = False


@given('a previously provisioned product exists with different parameters')
def step_given_product_exists_different_params(context):
    """Set up condition where a provisioned product exists with different parameters."""
    context.mock_service_catalog.describe_provisioned_product.return_value = {
        'ProvisionedProductDetail': {
            'Id': 'pp-existing123',
            'Name': context.task_attributes.get('launch_name', 'test-launch'),
            'Status': 'AVAILABLE',
            'ProductId': 'prod-test123',
            'ProvisioningArtifactId': 'pa-test123'
        }
    }
    
    # Mock CloudFormation to return different parameters
    context.mock_cloudformation.describe_stacks.return_value = {
        'Stacks': [{
            'Parameters': [
                {'ParameterKey': 'InstanceType', 'ParameterValue': 't3.small'},
                {'ParameterKey': 'Environment', 'ParameterValue': 'development'}
            ]
        }]
    }
    context.product_previously_provisioned = True
    context.parameters_differ = True


@given('a previously provisioned product exists with identical parameters and version')
def step_given_product_exists_identical_params(context):
    """Set up condition where a provisioned product exists with identical parameters."""
    context.mock_service_catalog.describe_provisioned_product.return_value = {
        'ProvisionedProductDetail': {
            'Id': 'pp-existing123',
            'Name': context.task_attributes.get('launch_name', 'test-launch'),
            'Status': 'AVAILABLE',
            'ProductId': 'prod-test123',
            'ProvisioningArtifactId': 'pa-test123'
        }
    }
    
    # Mock CloudFormation to return same parameters as in context
    launch_params = getattr(context, 'launch_parameters', {})
    cfn_params = [{'ParameterKey': k, 'ParameterValue': v} for k, v in launch_params.items()]
    context.mock_cloudformation.describe_stacks.return_value = {
        'Stacks': [{
            'Parameters': cfn_params
        }]
    }
    context.product_previously_provisioned = True
    context.parameters_differ = False


@given('a previously provisioned product exists in TAINTED state')
def step_given_product_exists_tainted(context):
    """Set up condition where a provisioned product exists in TAINTED state."""
    context.mock_service_catalog.describe_provisioned_product.return_value = {
        'ProvisionedProductDetail': {
            'Id': 'pp-tainted123',
            'Name': context.task_attributes.get('launch_name', 'test-launch'),
            'Status': 'TAINTED',
            'ProductId': 'prod-test123',
            'ProvisioningArtifactId': 'pa-test123'
        }
    }
    context.product_previously_provisioned = True
    context.product_is_tainted = True


@given('a provisioned product exists that is currently under change')
def step_given_product_under_change(context):
    """Set up condition where a provisioned product is under change."""
    # First call returns UNDER_CHANGE, second call returns AVAILABLE
    context.mock_service_catalog.describe_provisioned_product.side_effect = [
        {
            'ProvisionedProductDetail': {
                'Id': 'pp-changing123',
                'Name': context.task_attributes.get('launch_name', 'test-launch'),
                'Status': 'UNDER_CHANGE',
                'ProductId': 'prod-test123',
                'ProvisioningArtifactId': 'pa-test123'
            }
        },
        {
            'ProvisionedProductDetail': {
                'Id': 'pp-changing123',
                'Name': context.task_attributes.get('launch_name', 'test-launch'),
                'Status': 'AVAILABLE',
                'ProductId': 'prod-test123',
                'ProvisioningArtifactId': 'pa-test123'
            }
        }
    ]
    context.product_under_change = True


@given('an existing CloudFormation stack exists')
def step_given_cfn_stack_exists(context):
    """Set up condition where a CloudFormation stack exists."""
    stack_name = context.task_attributes.get('stack_name', 'test-stack')
    context.mock_cloudformation.describe_stacks.return_value = {
        'Stacks': [{
            'StackName': stack_name,
            'StackStatus': 'CREATE_COMPLETE',
            'StackId': f'arn:aws:cloudformation:us-east-1:123456789012:stack/{stack_name}/uuid'
        }]
    }
    context.stack_exists = True


@given('no stack exists with the specified name')
def step_given_no_stack_exists(context):
    """Set up condition where no CloudFormation stack exists."""
    context.mock_cloudformation.describe_stacks.side_effect = Exception("Stack does not exist")
    context.stack_exists = False


@given('no organizational unit exists with the specified name in the parent')
def step_given_no_ou_exists(context):
    """Set up condition where no organizational unit exists."""
    context.mock_organizations.list_children.return_value = {'Children': []}
    context.ou_exists = False


@given('an organizational unit already exists with the specified name in the parent')
def step_given_ou_exists(context):
    """Set up condition where an organizational unit already exists."""
    ou_name = context.task_attributes.get('name', 'TestOU')
    context.mock_organizations.list_children.return_value = {
        'Children': [{'Id': 'ou-existing123', 'Type': 'ORGANIZATIONAL_UNIT'}]
    }
    context.mock_organizations.describe_organizational_unit.return_value = {
        'OrganizationalUnit': {
            'Id': 'ou-existing123',
            'Name': ou_name
        }
    }
    context.ou_exists = True


@given('the parent organizational unit does not exist')
def step_given_parent_ou_not_exists(context):
    """Set up condition where parent organizational unit does not exist."""
    context.mock_organizations.describe_organizational_unit.side_effect = Exception("OrganizationalUnitNotFoundException")
    context.parent_ou_exists = False


@given('the parent organizational unit task must complete first')
def step_given_parent_ou_task_dependency(context):
    """Set up dependency on parent OU task."""
    context.parent_ou_task_required = True


@given('SNS notifications are enabled')
def step_given_sns_enabled(context):
    """Set up SNS notifications enabled."""
    if hasattr(context.current_task, 'should_use_sns'):
        context.current_task.should_use_sns = True
    context.sns_enabled = True


@given('a CloudFormation service role is configured')
def step_given_cfn_service_role(context):
    """Set up CloudFormation service role configuration."""
    context.cfn_service_role_configured = True


@given('the spoke portfolio exists with ID "{portfolio_id}"')
def step_given_spoke_portfolio_exists(context, portfolio_id):
    """Set up spoke portfolio existence."""
    context.spoke_portfolio_id = portfolio_id
    context.spoke_portfolio_exists = True


@given('the hub portfolio exists with ID "{portfolio_id}"')
def step_given_hub_portfolio_exists(context, portfolio_id):
    """Set up hub portfolio existence."""
    context.hub_portfolio_id = portfolio_id
    context.hub_portfolio_exists = True


@given('the hub portfolio contains products not present in spoke portfolio')
def step_given_hub_has_new_products(context):
    """Set up condition where hub has products not in spoke."""
    context.hub_has_new_products = True
    
    # Mock the task's dependency methods to return different product lists
    if hasattr(context.current_task, 'get_output_from_reference_dependency'):
        context.current_task.get_output_from_reference_dependency.side_effect = [
            CommonTestData.PORTFOLIO_DATA['spoke_portfolio'],  # spoke portfolio details
            {},  # spoke products (empty)
            CommonTestData.PORTFOLIO_DATA['hub_portfolio'],    # hub portfolio details
            CommonTestData.PRODUCT_DATA  # hub products (has products)
        ]


@given('the spoke portfolio already contains all products from the hub portfolio')
def step_given_spoke_has_all_products(context):
    """Set up condition where spoke already has all hub products."""
    context.spoke_has_all_products = True
    
    # Mock the task's dependency methods to return same product lists
    if hasattr(context.current_task, 'get_output_from_reference_dependency'):
        context.current_task.get_output_from_reference_dependency.side_effect = [
            CommonTestData.PORTFOLIO_DATA['spoke_portfolio'],  # spoke portfolio details
            CommonTestData.PRODUCT_DATA,  # spoke products (same as hub)
            CommonTestData.PORTFOLIO_DATA['hub_portfolio'],    # hub portfolio details
            CommonTestData.PRODUCT_DATA   # hub products (same as spoke)
        ]


@given('the hub portfolio contains products with multiple versions')
def step_given_hub_has_multiple_versions(context):
    """Set up condition where hub has products with multiple versions."""
    context.hub_has_multiple_versions = True


@given('the spoke portfolio has outdated versions of some products')
def step_given_spoke_has_outdated_versions(context):
    """Set up condition where spoke has outdated product versions."""
    context.spoke_has_outdated_versions = True


@given('the spoke portfolio is empty (contains no products)')
def step_given_spoke_portfolio_empty(context):
    """Set up condition where spoke portfolio is empty."""
    context.spoke_portfolio_empty = True
    
    # Mock the task's dependency methods
    if hasattr(context.current_task, 'get_output_from_reference_dependency'):
        context.current_task.get_output_from_reference_dependency.side_effect = [
            CommonTestData.PORTFOLIO_DATA['spoke_portfolio'],  # spoke portfolio details
            {},  # spoke products (empty)
            CommonTestData.PORTFOLIO_DATA['hub_portfolio'],    # hub portfolio details
            CommonTestData.PRODUCT_DATA   # hub products (has products)
        ]


@given('the hub portfolio is in a different region')
def step_given_hub_different_region(context):
    """Set up condition where hub portfolio is in different region."""
    context.hub_different_region = True


@given('both portfolios exist and are accessible')
def step_given_both_portfolios_accessible(context):
    """Set up condition where both portfolios are accessible."""
    context.hub_portfolio_accessible = True
    context.spoke_portfolio_accessible = True


@given('the spoke portfolio exists')
def step_given_spoke_portfolio_exists_simple(context):
    """Set up simple spoke portfolio existence."""
    context.spoke_portfolio_exists = True


@given('the hub portfolio reference is invalid or inaccessible')
def step_given_hub_portfolio_invalid(context):
    """Set up condition where hub portfolio reference is invalid."""
    context.hub_portfolio_accessible = False
    
    # Make the dependency method raise an error
    if hasattr(context.current_task, 'get_output_from_reference_dependency'):
        context.current_task.get_output_from_reference_dependency.side_effect = Exception("Invalid reference")


@given('a large object exists in the bucket')
def step_given_large_s3_object(context):
    """Set up condition where a large S3 object exists."""
    # Create a mock response with large content
    large_content = "x" * 1000000  # 1MB of data
    mock_body = MagicMock()
    mock_body.read.return_value = large_content.encode()
    
    context.mock_s3.get_object.return_value = {
        'Body': mock_body,
        'ContentLength': len(large_content)
    }
    context.large_object_exists = True


@given('a binary object (image file) exists in the bucket')
def step_given_binary_object(context):
    """Set up condition where a binary object exists."""
    # Create mock binary content
    binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'  # PNG header
    mock_body = MagicMock()
    mock_body.read.return_value = binary_content
    
    context.mock_s3.get_object.return_value = {
        'Body': mock_body,
        'ContentType': 'image/png'
    }
    context.binary_object_exists = True


@given('access to the object is denied due to insufficient permissions')
def step_given_s3_access_denied(context):
    """Set up condition where S3 access is denied."""
    context.mock_s3.get_object.side_effect = Exception("AccessDenied")
    context.s3_access_denied = True


@given('a StackSet instance exists in the target account')
def step_given_stackset_instance_exists(context):
    """Set up condition where a StackSet instance exists."""
    context.stackset_instance_exists = True
    context.mock_cloudformation.describe_stack_set_operation.return_value = {
        'StackSetOperation': {
            'Status': 'SUCCEEDED'
        }
    }


@given('service control policies are enabled in the organization')
def step_given_scp_enabled(context):
    """Set up condition where SCPs are enabled."""
    context.scp_enabled = True


# Additional common precondition steps
@given('I have proper client configurations')
def step_given_proper_client_configurations(context):
    """Set up proper client configurations."""
    context.proper_client_configurations = True


@given('I have a CodeBuild project configured')
def step_given_codebuild_project_configured(context):
    """Set up CodeBuild project configuration."""
    context.codebuild_project_configured = True


@given('the project has environment variables defined')
def step_given_project_env_vars_defined(context):
    """Set up project with environment variables."""
    context.project_env_vars_defined = True


@given('the project has environment variables:')
def step_given_project_env_vars_table(context):
    """Set up project environment variables from table."""
    # Handle different column naming patterns
    if 'env_var_name' in context.table.headings:
        env_vars = {row['env_var_name']: row['env_var_value'] for row in context.table}
    elif 'name' in context.table.headings and 'type' in context.table.headings:
        env_vars = {row['name']: row['type'] for row in context.table}
    else:
        # Fallback - use first two columns
        env_vars = {row[context.table.headings[0]]: row[context.table.headings[1]] for row in context.table}
    context.project_env_vars = env_vars


@given('I have parameter values:')
def step_given_parameter_values(context):
    """Set up parameter values from table."""
    # Handle different column naming patterns
    if 'parameter_name' in context.table.headings:
        param_values = {row['parameter_name']: row['parameter_value'] for row in context.table}
    else:
        # Use first two columns as key-value pairs (like in the test table)
        param_values = {row[context.table.headings[0]]: row[context.table.headings[1]] for row in context.table}
    context.parameter_values = param_values


@given('the stack exists and is in a deletable state')
def step_given_stack_exists_deletable(context):
    """Set up stack in deletable state."""
    context.stack_exists = True
    context.stack_deletable = True


@given('the stack does not exist')
def step_given_stack_does_not_exist(context):
    """Set up scenario where stack does not exist."""
    context.stack_exists = False


@given('the stack has dependent resources or outputs referenced by other stacks')
def step_given_stack_has_dependencies(context):
    """Set up stack with dependencies."""
    context.stack_has_dependencies = True


@given('the stack contains resources with DeletionPolicy: Retain')
def step_given_stack_has_retain_policy(context):
    """Set up stack with retain deletion policy."""
    context.stack_has_retain_policy = True


@given('the current account ID is "{account_id}"')
def step_given_current_account_id(context, account_id):
    """Set up current account ID."""
    context.current_account_id = account_id


