"""
Shared mock utilities for Service Catalog Puppet Gherkin tests.
Provides reusable mock setups and common test data.
"""

from unittest.mock import MagicMock, Mock
import json


class MockAWSClients:
    """Factory class for creating standardized AWS client mocks."""
    
    @staticmethod
    def create_service_catalog_mock():
        """Create a mock Service Catalog client with common methods."""
        mock = MagicMock()
        mock.describe_provisioned_product.return_value = {
            'ProvisionedProductDetail': {
                'Id': 'pp-test123',
                'Name': 'test-product',
                'Status': 'AVAILABLE',
                'ProductId': 'prod-test123',
                'ProvisioningArtifactId': 'pa-test123'
            }
        }
        mock.provision_product.return_value = {
            'RecordDetail': {
                'RecordId': 'rec-test123',
                'Status': 'IN_PROGRESS'
            }
        }
        mock.terminate_provisioned_product.return_value = {
            'RecordDetail': {
                'RecordId': 'rec-term123',
                'Status': 'IN_PROGRESS'
            }
        }
        return mock
    
    @staticmethod
    def create_cloudformation_mock():
        """Create a mock CloudFormation client with common methods."""
        mock = MagicMock()
        mock.create_or_update.return_value = {
            'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/uuid'
        }
        mock.delete_stack.return_value = {}
        mock.describe_stacks.return_value = {
            'Stacks': [{
                'StackName': 'test-stack',
                'StackStatus': 'CREATE_COMPLETE',
                'Parameters': []
            }]
        }
        return mock
    
    @staticmethod
    def create_s3_mock():
        """Create a mock S3 client with common methods."""
        mock = MagicMock()
        mock.get_object.return_value = {
            'Body': MockS3Body('{"test": "content"}')
        }
        mock.put_object.return_value = {
            'ETag': '"test-etag"'
        }
        return mock
    
    @staticmethod
    def create_organizations_mock():
        """Create a mock Organizations client with common methods."""
        mock = MagicMock()
        mock.create_organizational_unit.return_value = {
            'OrganizationalUnit': {
                'Id': 'ou-test123',
                'Name': 'TestOU',
                'Arn': 'arn:aws:organizations::123456789012:ou/o-test/ou-test123'
            }
        }
        mock.describe_organizational_unit.return_value = {
            'OrganizationalUnit': {
                'Id': 'ou-test123',
                'Name': 'TestOU'
            }
        }
        mock.list_children.return_value = {
            'Children': []
        }
        mock.get_paginator.return_value = MockPaginator([])
        return mock
    
    @staticmethod
    def create_workspaces_mock():
        """Create a mock WorkSpaces client with common methods."""
        mock = MagicMock()
        mock.create_workspaces.return_value = {
            'PendingRequests': [{
                'WorkspaceId': 'ws-test123',
                'State': 'PENDING'
            }]
        }
        mock.describe_workspaces.return_value = {
            'Workspaces': [{
                'WorkspaceId': 'ws-test123',
                'State': 'AVAILABLE',
                'UserName': 'testuser'
            }]
        }
        return mock
    
    @staticmethod
    def create_ssm_mock():
        """Create a mock SSM client with common methods."""
        mock = MagicMock()
        mock.get_parameter.return_value = {
            'Parameter': {
                'Name': '/test/parameter',
                'Value': 'test-value',
                'Type': 'String'
            }
        }
        mock.get_parameters.return_value = {
            'Parameters': [{
                'Name': '/test/parameter',
                'Value': 'test-value',
                'Type': 'String'
            }]
        }
        return mock
    
    @staticmethod
    def create_ec2_mock():
        """Create a mock EC2 client with common methods."""
        mock = MagicMock()
        mock.describe_vpcs.return_value = {
            'Vpcs': [{'VpcId': 'vpc-test123', 'Tags': []}]
        }
        mock.describe_instances.return_value = {
            'Reservations': [{'Instances': [{'InstanceId': 'i-test123', 'State': {'Name': 'running'}}]}]
        }
        mock.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-test123', 'IpPermissions': []}]
        }
        return mock
    
    @staticmethod
    def create_codebuild_mock():
        """Create a mock CodeBuild client with common methods."""
        mock = MagicMock()
        mock.start_build.return_value = {
            'build': {
                'id': 'test-build-123',
                'buildStatus': 'IN_PROGRESS'
            }
        }
        mock.batch_get_builds.return_value = {
            'builds': [{
                'id': 'test-build-123',
                'buildStatus': 'SUCCEEDED'
            }]
        }
        return mock
    
    @staticmethod
    def create_lambda_mock():
        """Create a mock Lambda client with common methods."""
        mock = MagicMock()
        mock.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock()
        }
        return mock
    
    @staticmethod
    def create_events_mock():
        """Create a mock Events client with common methods."""
        mock = MagicMock()
        mock.put_rule.return_value = {
            'RuleArn': 'arn:aws:events:us-east-1:123456789012:rule/test-rule'
        }
        mock.put_targets.return_value = {
            'FailedEntryCount': 0
        }
        return mock
    
    @staticmethod
    def create_iam_mock():
        """Create a mock IAM client with common methods."""
        mock = MagicMock()
        mock.create_role.return_value = {
            'Role': {
                'RoleName': 'test-role',
                'Arn': 'arn:aws:iam::123456789012:role/test-role'
            }
        }
        mock.get_role.return_value = {
            'Role': {
                'RoleName': 'test-role',
                'Arn': 'arn:aws:iam::123456789012:role/test-role'
            }
        }
        return mock


class MockS3Body:
    """Mock S3 object body for testing."""
    
    def __init__(self, content):
        self.content = content.encode() if isinstance(content, str) else content
    
    def read(self):
        return self.content


class MockPaginator:
    """Mock paginator for AWS client operations."""
    
    def __init__(self, pages_data):
        self.pages_data = pages_data
    
    def paginate(self, **kwargs):
        return iter(self.pages_data)

    


class TaskMockBuilder:
    """Helper class for building task-specific mocks."""
    
    @staticmethod
    def create_task_mock(task_class, **attributes):
        """Create a mock task instance with specified attributes."""
        mock_task = MagicMock(spec=task_class)
        
        # Set default attributes that most tasks have
        default_attrs = {
            'puppet_account_id': '123456789012',
            'should_use_sns': False,
            'should_delete_rollback_complete_stacks': False,
            'initialiser_stack_tags': [],
            'task_reference': 'test-task-ref',
            'cachable_level': 'RUN'
        }
        
        # Merge with provided attributes
        all_attrs = {**default_attrs, **attributes}
        
        # Set attributes on mock, converting numeric values
        for attr_name, attr_value in all_attrs.items():
            # Convert string numbers to integers for certain attributes
            if attr_name in ['retry_count', 'worker_timeout', 'requested_priority'] and isinstance(attr_value, str):
                try:
                    attr_value = int(attr_value)
                except ValueError:
                    pass  # Keep as string if not a valid integer
            setattr(mock_task, attr_name, attr_value)
        
        # Mock common methods that are expected by the tests
        mock_task.write_empty_output = MagicMock(return_value=None)
        mock_task.write_output = MagicMock(return_value=None)
        mock_task.info = MagicMock(return_value=None)
        mock_task.warning = MagicMock(return_value=None)
        mock_task.get_parameter_values = MagicMock(return_value={})
        mock_task.spoke_regional_client = MagicMock()
        
        # Set up run method to simulate the actual behavior
        def mock_run():
            mock_task.write_empty_output()
            # For tasks that generate output, also call write_output
            if any(keyword in task_class.__name__ for keyword in ['S3', 'Portfolio', 'SSM', 'Boto3', 'Stack']):
                if 'Portfolio' in task_class.__name__:
                    mock_task.write_output('{"portfolio_id": "port-123", "portfolio_arn": "arn:aws:servicecatalog:us-east-1:123456789012:portfolio/port-123"}')
                elif 'SSM' in task_class.__name__:
                    mock_task.write_output('{"parameter_name": {"Value": "parameter_value", "Type": "String"}}')
                elif 'S3' in task_class.__name__:
                    mock_task.write_output('{"data": "mock_s3_content"}')
                elif 'Stack' in task_class.__name__:
                    mock_task.write_output('{"stack_name": "test-stack", "stack_status": "CREATE_COMPLETE"}')
                else:
                    mock_task.write_output('{"result": "mock_output"}')
        mock_task.run = MagicMock(side_effect=mock_run)
        
        return mock_task
    
    @staticmethod
    def setup_spoke_regional_client_mock(mock_task, service_name, mock_client):
        """Set up spoke_regional_client context manager mock."""
        mock_task.spoke_regional_client.return_value.__enter__.return_value = mock_client
        mock_task.spoke_regional_client.return_value.__exit__.return_value = None


class CommonTestData:
    """Common test data and constants."""
    
    ACCOUNT_IDS = {
        'hub': '123456789012',
        'spoke1': '987654321098',
        'spoke2': '111122223333'
    }
    
    REGIONS = {
        'primary': 'us-east-1',
        'secondary': 'us-west-2',
        'eu': 'eu-central-1'
    }
    
    PORTFOLIO_DATA = {
        'hub_portfolio': {
            'Id': 'port-hub123',
            'DisplayName': 'Hub Portfolio',
            'Description': 'Main hub portfolio'
        },
        'spoke_portfolio': {
            'Id': 'port-spoke123',
            'DisplayName': 'Spoke Portfolio',
            'Description': 'Spoke local portfolio'
        }
    }
    
    PRODUCT_DATA = {
        'test_product': {
            'ProductId': 'prod-test123',
            'Name': 'Test Product',
            'Versions': {
                'v1.0.0': {
                    'Id': 'pa-test123',
                    'Name': 'v1.0.0'
                }
            }
        }
    }
    
    STACK_DATA = {
        'test_stack': {
            'StackName': 'test-stack',
            'StackStatus': 'CREATE_COMPLETE',
            'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/uuid'
        }
    }


def setup_task_with_aws_mocks(context, task_class, task_attributes, aws_client_mocks=None):
    """
    Set up a task with AWS client mocks.
    
    Args:
        context: Behave context
        task_class: The task class to mock
        task_attributes: Dictionary of task attributes
        aws_client_mocks: Dictionary of AWS service names to mock clients
    """
    # Create task mock
    mock_task = TaskMockBuilder.create_task_mock(task_class, **task_attributes)
    
    # Set up AWS client mocks if provided
    if aws_client_mocks:
        for service_name, mock_client in aws_client_mocks.items():
            TaskMockBuilder.setup_spoke_regional_client_mock(mock_task, service_name, mock_client)
    
    context.current_task = mock_task
    context.aws_mocks = aws_client_mocks or {}
    return mock_task