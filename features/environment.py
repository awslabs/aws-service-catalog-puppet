"""
Behave environment configuration for Service Catalog Puppet tests.
Sets up AWS mocking and test context.
"""

import os
import tempfile
from unittest.mock import Mock, patch
import boto3
from moto import mock_aws


def before_all(context):
    """
    Set up global test environment before all scenarios.
    """
    # Set up AWS mocking with the new mock_aws context manager approach
    context.aws_mock = mock_aws()
    context.aws_mock.start()
    
    # Set up AWS credentials for moto
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Create test working directory
    context.test_dir = tempfile.mkdtemp()
    context.manifest_files_path = os.path.join(context.test_dir, 'manifest_files')
    os.makedirs(context.manifest_files_path, exist_ok=True)
    os.makedirs(os.path.join(context.manifest_files_path, 'tasks'), exist_ok=True)
    
    # Initialize task registry
    context.tasks = {}
    context.task_outputs = {}


def after_all(context):
    """
    Clean up after all scenarios.
    """
    # Stop AWS mock
    context.aws_mock.stop()
    
    # Clean up test directory
    import shutil
    if hasattr(context, 'test_dir'):
        shutil.rmtree(context.test_dir, ignore_errors=True)


def before_scenario(context, scenario):
    """
    Set up before each scenario.
    """
    # Reset task registry for each scenario
    context.current_task = None
    context.task_parameters = {}
    context.task_result = None
    context.task_error = None
    
    # Mock AWS clients to avoid real AWS calls
    context.aws_clients = {}
    
    # Create default test S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-deployment-bucket')
    s3.create_bucket(Bucket='my-deployment-bucket')


def after_scenario(context, scenario):
    """
    Clean up after each scenario.
    """
    # Clear any scenario-specific state
    context.current_task = None
    context.task_parameters = {}
    context.task_result = None
    context.task_error = None


def before_step(context, step):
    """
    Set up before each step.
    """
    pass


def after_step(context, step):
    """
    Clean up after each step.
    """
    pass