Feature: Prepare C7N Hub Account Task
  As a Service Catalog Puppet user
  I want to set up the Cloud Custodian hub account infrastructure
  So that I can centrally manage and execute Cloud Custodian policies across my organization

  Background:
    Given I have the necessary AWS permissions
    And I have administrator access to the hub account
    And I have CloudFormation deployment capabilities
    And I have the organization ID and custodian configuration parameters

  Scenario: Prepare C7N hub account with standard c7n
    Given a PrepareC7NHubAccountTask with the following attributes:
      | attribute           | value                           |
      | custodian_region    | us-east-1                       |
      | c7n_version         | 0.9.20                          |
      | c7n_org_version     |                                 |
      | organization        | o-abc1234567                    |
      | role_name           | CustodianExecutionRole          |
      | role_path           | /service-roles/                 |
      | schedule_expression | cron(0 2 * * ? *)              |
    When I run the task
    Then a CloudFormation stack should be created with name "servicecatalog-puppet-c7n-eventbus"
    And an EventBus policy should allow organization accounts to put events
    And a C7NRunRole should be created for CodeBuild execution
    And a C7NEventRuleRunRole should be created for EventBridge
    And an S3 bucket should be created for c7n policies and artifacts
    And a CodeBuild project should be created with c7n installation
    And an EventBridge rule should be created with the specified schedule
    And the output should contain the c7n account ID

  Scenario: Prepare C7N hub account with c7n-org
    Given a PrepareC7NHubAccountTask with the following attributes:
      | attribute           | value                           |
      | custodian_region    | eu-west-1                       |
      | c7n_version         | 0.9.20                          |
      | c7n_org_version     | 0.6.15                          |
      | organization        | o-xyz9876543                    |
      | role_name           | C7NCustodianRole                |
      | role_path           | /custodian/                     |
      | schedule_expression | cron(0 6 * * ? *)              |
    When I run the task
    Then the CodeBuild project should install c7n-org instead of c7n
    And the build spec should use "c7n-org run" command
    And the build spec should reference accounts.yaml configuration file
    And the S3 bucket should be named with the custodian region
    And the EventBridge rule should be enabled with the daily schedule

  Scenario: Prepare C7N hub account without scheduled execution
    Given a PrepareC7NHubAccountTask with the following attributes:
      | attribute           | value                           |
      | custodian_region    | ap-southeast-1                  |
      | c7n_version         | 0.9.18                          |
      | c7n_org_version     |                                 |
      | organization        | o-def5678901                    |
      | role_name           | SecurityCustodianRole           |
      | role_path           | /security/                      |
      | schedule_expression |                                 |
    When I run the task
    Then the EventBridge rule should be created in DISABLED state
    And c7n policies will only run when triggered manually
    And all other infrastructure should be created normally

  Scenario: Verify IAM roles and permissions
    Given a PrepareC7NHubAccountTask with the following attributes:
      | attribute           | value                           |
      | custodian_region    | us-west-2                       |
      | c7n_version         | 0.9.21                          |
      | c7n_org_version     |                                 |
      | organization        | o-ghi2345678                    |
      | role_name           | ComplianceCustodianRole         |
      | role_path           | /compliance/                    |
      | schedule_expression | cron(0 0 * * ? *)              |
    When I run the task
    Then the C7NRunRole should have permissions to:
      | permission_type     | resource_pattern                                    |
      | sts:AssumeRole      | arn:*:iam::*:role/compliance/ComplianceCustodianRole |
      | logs:*              | /aws/codebuild/servicecatalog-puppet-deploy-c7n     |
      | ssm:GetParameters   | servicecatalog-puppet/aws-c7n-lambdas/*             |
      | s3:GetObject*       | sc-puppet-c7n-artifacts-*/latest                    |
    And the C7NEventRuleRunRole should have codebuild:StartBuild permission
    And the EventBus policy should allow the specified organization

  Scenario: Verify S3 bucket configuration
    Given a PrepareC7NHubAccountTask with the following attributes:
      | attribute           | value                           |
      | custodian_region    | ca-central-1                    |
      | c7n_version         | 0.9.19                          |
      | c7n_org_version     |                                 |
      | organization        | o-jkl3456789                    |
      | role_name           | AuditCustodianRole              |
      | role_path           | /audit/                         |
      | schedule_expression | cron(0 12 * * ? *)             |
    When I run the task
    Then the S3 bucket should be named "sc-puppet-c7n-artifacts-{AccountId}-ca-central-1"
    And the bucket should have versioning enabled
    And the bucket should have AES256 encryption
    And the bucket should block all public access
    And the bucket should have ServiceCatalogPuppet:Actor tag

  Scenario: Verify CodeBuild project configuration
    Given a PrepareC7NHubAccountTask with the following attributes:
      | attribute           | value                           |
      | custodian_region    | eu-central-1                    |
      | c7n_version         | 0.9.22                          |
      | c7n_org_version     |                                 |
      | organization        | o-mno4567890                    |
      | role_name           | GovernanceCustodianRole         |
      | role_path           | /governance/                    |
      | schedule_expression | cron(0 18 * * ? *)             |
    When I run the task
    Then the CodeBuild project should be named "servicecatalog-puppet-deploy-c7n"
    And the project should have 8 hours timeout
    And the project should use BUILD_GENERAL1_SMALL compute type
    And the project should have environment variables for c7n version and account details
    And the project should reference SSM parameters for regions and role ARN

  Scenario: Handle hub account preparation failure
    Given a PrepareC7NHubAccountTask with the following attributes:
      | attribute           | value                           |
      | custodian_region    | invalid-region                  |
      | c7n_version         | invalid-version                 |
      | c7n_org_version     |                                 |
      | organization        | invalid-org-id                  |
      | role_name           | InvalidRole                     |
      | role_path           | /invalid/                       |
      | schedule_expression | invalid-cron                    |
    When I run the task
    And the CloudFormation deployment fails due to invalid parameters
    Then the task should handle the error appropriately
    And relevant error information should be logged