Feature: Provision Workspace Task
  As a Service Catalog Puppet user
  I want to provision AWS Workspaces
  So that I can deploy virtual desktop infrastructure as part of my managed workflows

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And AWS Workspaces service is available
    And the S3 bucket contains workspace artifacts

  Scenario: Provision workspace successfully
    Given a ProvisionWorkspaceTask with the following attributes:
      | attribute              | value                     |
      | workspace_name        | dev-workspace-001         |
      | region                | us-east-1                 |
      | account_id            | 123456789012              |
      | bucket                | my-workspace-artifacts    |
      | key                   | workspaces/dev-ws/v1.zip  |
      | version_id            | abc123def456              |
      | execution             | hub                       |
      | manifest_file_path    | /path/to/manifest.yaml    |
    When I run the task
    Then the workspace should be provisioned in the target account
    And the workspace artifacts should be downloaded from S3
    And the task should complete successfully

  Scenario: Provision workspace with launch parameters
    Given a ProvisionWorkspaceTask with the following attributes:
      | attribute              | value                     |
      | workspace_name        | prod-workspace-002        |
      | region                | us-west-2                 |
      | account_id            | 987654321098              |
      | bucket                | workspace-deployment-bucket |
      | key                   | workspaces/prod-ws/v2.zip |
      | version_id            | xyz789abc123              |
      | execution             | spoke                     |
      | manifest_file_path    | /path/to/manifest.yaml    |
    And launch parameters:
      | parameter_name    | parameter_value   |
      | BundleId         | wsb-12345678      |
      | DirectoryId      | d-123456789a      |
      | UserName         | testuser          |
    When I run the task
    Then the workspace should be provisioned with the specified parameters
    And the correct bundle and directory should be used
    And the task should complete successfully

  Scenario: Provision workspace with SSM parameter inputs
    Given a ProvisionWorkspaceTask with the following attributes:
      | attribute              | value                     |
      | workspace_name        | ssm-workspace-003         |
      | region                | eu-central-1              |
      | account_id            | 111122223333              |
      | bucket                | workspace-configs         |
      | key                   | workspaces/ssm-ws/v1.zip  |
      | version_id            | def456ghi789              |
      | execution             | hub                       |
      | manifest_file_path    | /path/to/manifest.yaml    |
      | ssm_param_inputs      | ["/workspace/directory/id", "/workspace/bundle/id"] |
    When I run the task
    Then the SSM parameters should be retrieved and used
    And the workspace should be provisioned with SSM parameter values
    And the task should complete successfully

  Scenario: Provision workspace with custom priority and retry settings
    Given a ProvisionWorkspaceTask with the following attributes:
      | attribute              | value                     |
      | workspace_name        | priority-workspace-004    |
      | region                | ap-southeast-1            |
      | account_id            | 444455556666              |
      | bucket                | workspace-artifacts       |
      | key                   | workspaces/priority-ws/v1.zip |
      | version_id            | ghi789jkl012              |
      | execution             | spoke                     |
      | manifest_file_path    | /path/to/manifest.yaml    |
      | retry_count           | 3                         |
      | worker_timeout        | 900                       |
      | requested_priority    | 10                        |
    When I run the task
    Then the task should have priority 10
    And the task should be configured for 3 retries
    And the worker timeout should be 900 seconds
    And the workspace should be provisioned successfully

  Scenario: Provision workspace with manifest and account parameters
    Given a ProvisionWorkspaceTask with the following attributes:
      | attribute              | value                     |
      | workspace_name        | config-workspace-005      |
      | region                | ca-central-1              |
      | account_id            | 777788889999              |
      | bucket                | workspace-deployment      |
      | key                   | workspaces/config-ws/v2.zip |
      | version_id            | jkl012mno345              |
      | execution             | hub                       |
      | manifest_file_path    | /path/to/manifest.yaml    |
    And manifest parameters:
      | parameter_name    | parameter_value   |
      | WorkspaceType    | Standard          |
      | Region           | ca-central-1      |
    And account parameters:
      | parameter_name    | parameter_value   |
      | VpcId            | vpc-12345678      |
      | SubnetIds        | subnet-12345,subnet-67890 |
    When I run the task
    Then the workspace should be provisioned with manifest and account parameters
    And the correct VPC and subnets should be used
    And the task should complete successfully

  Scenario: Handle workspace provisioning with S3 artifact processing
    Given a ProvisionWorkspaceTask with the following attributes:
      | attribute              | value                     |
      | workspace_name        | artifact-workspace-006    |
      | region                | us-east-1                 |
      | account_id            | 123456789012              |
      | bucket                | workspace-zip-artifacts   |
      | key                   | workspaces/complex/v3.zip |
      | version_id            | mno345pqr678              |
      | execution             | hub                       |
      | manifest_file_path    | /path/to/manifest.yaml    |
    When I run the task
    Then the S3 zip artifact should be downloaded and extracted
    And the workspace configuration should be processed from the artifact
    And the workspace should be provisioned using the extracted configuration
    And SSM parameter outputs should be processed if specified