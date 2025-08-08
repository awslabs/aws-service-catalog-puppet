"""
Behave environment configuration for Service Catalog Puppet tests.
Sets up AWS mocking and test context.
"""

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock


def before_all(context):
    """
    Set up global test environment before all scenarios.
    """
    # Create test working directory
    context.test_dir = tempfile.mkdtemp()
    context.manifest_files_path = os.path.join(context.test_dir, 'manifest_files')
    os.makedirs(context.manifest_files_path, exist_ok=True)
    os.makedirs(os.path.join(context.manifest_files_path, 'tasks'), exist_ok=True)
    
    # Initialize task registry
    context.tasks = {}
    context.task_outputs = {}
    
    # Set up shared mock patches that will be used across tests
    context.patches = []


def after_all(context):
    """
    Clean up after all scenarios.
    """
    # Stop all patches
    for patcher in getattr(context, 'patches', []):
        patcher.stop()
    
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
    context.task_attributes = {}
    
    # Mock AWS clients - use normal Python mocks instead of moto
    context.mock_aws_clients = {}
    context.mock_responses = {}
    
    # Set up commonly used mock clients
    context.mock_service_catalog = MagicMock()
    context.mock_cloudformation = MagicMock()
    context.mock_s3 = MagicMock()
    context.mock_organizations = MagicMock()
    context.mock_workspaces = MagicMock()
    context.mock_ssm = MagicMock()
    
    # Store mocks in a registry for easy access
    context.mock_aws_clients = {
        'servicecatalog': context.mock_service_catalog,
        'cloudformation': context.mock_cloudformation,
        's3': context.mock_s3,
        'organizations': context.mock_organizations,
        'workspaces': context.mock_workspaces,
        'ssm': context.mock_ssm,
    }


def after_scenario(context, scenario):
    """
    Clean up after each scenario.
    """
    # Clear any scenario-specific state
    context.current_task = None
    context.task_parameters = {}
    context.task_result = None
    context.task_error = None
    context.task_attributes = {}
    
    # Reset all mocks
    for mock_client in context.mock_aws_clients.values():
        mock_client.reset_mock()


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