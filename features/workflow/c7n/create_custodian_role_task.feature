Feature: Create Custodian Role Task
  As a Service Catalog Puppet user
  I want to create IAM roles for Cloud Custodian (c7n) in target accounts
  So that Cloud Custodian can execute policies with appropriate permissions

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have CloudFormation deployment capabilities

  Scenario: Create custodian role successfully
    Given a CreateCustodianRoleTask with the following attributes:
      | attribute                  | value                                           |
      | c7n_account_id            | 123456789012                                    |
      | role_name                 | CustodianExecutionRole                          |
      | role_path                 | /service-roles/                                 |
      | role_managed_policy_arns  | ["arn:aws:iam::aws:policy/ReadOnlyAccess"]     |
    When I run the task
    Then a CloudFormation stack should be created with name "servicecatalog-puppet-c7n-custodian"
    And the IAM role should be created with the specified name and path
    And the role should have the managed policy ARNs attached
    And the role should allow Lambda service to assume it
    And the role should allow the c7n account to assume it
    And an empty output file should be written

  Scenario: Create custodian role with multiple managed policies
    Given a CreateCustodianRoleTask with the following attributes:
      | attribute                  | value                                                                    |
      | c7n_account_id            | 987654321098                                                             |
      | role_name                 | C7NCustodianRole                                                         |
      | role_path                 | /custodian/                                                              |
      | role_managed_policy_arns  | ["arn:aws:iam::aws:policy/ReadOnlyAccess", "arn:aws:iam::aws:policy/PowerUserAccess"] |
    When I run the task
    Then the CloudFormation template should include both managed policies
    And the IAM role should have both policies attached
    And the assume role policy should include both Lambda and c7n account principals
    And the stack should be created with CAPABILITY_NAMED_IAM

  Scenario: Create custodian role with custom role path
    Given a CreateCustodianRoleTask with the following attributes:
      | attribute                  | value                                           |
      | c7n_account_id            | 111122223333                                    |
      | role_name                 | SecurityCustodianRole                           |
      | role_path                 | /security/custodian/                            |
      | role_managed_policy_arns  | ["arn:aws:iam::aws:policy/SecurityAudit"]      |
    When I run the task
    Then the IAM role should be created with path "/security/custodian/"
    And the role should be accessible at the specified path
    And proper CloudFormation tags should be applied

  Scenario: Handle CloudFormation stack update
    Given a CreateCustodianRoleTask with the following attributes:
      | attribute                  | value                                           |
      | c7n_account_id            | 444455556666                                    |
      | role_name                 | UpdatedCustodianRole                            |
      | role_path                 | /updated/                                       |
      | role_managed_policy_arns  | ["arn:aws:iam::aws:policy/ReadOnlyAccess"]     |
    And a CloudFormation stack already exists with the same name
    When I run the task
    Then the existing stack should be updated instead of created
    And the role configuration should be updated to match the new parameters
    And change sets should not be used for the update
    And an empty output file should be written

  Scenario: Create custodian role with SNS notifications
    Given a CreateCustodianRoleTask with the following attributes:
      | attribute                  | value                                           |
      | c7n_account_id            | 777788889999                                    |
      | role_name                 | NotificationCustodianRole                       |
      | role_path                 | /notifications/                                 |
      | role_managed_policy_arns  | ["arn:aws:iam::aws:policy/ReadOnlyAccess"]     |
    And SNS notifications are enabled
    When I run the task
    Then the CloudFormation stack should include notification ARNs
    And notifications should be sent to the regional events topic
    And the stack should complete successfully

  Scenario: Handle role creation failure
    Given a CreateCustodianRoleTask with the following attributes:
      | attribute                  | value                                           |
      | c7n_account_id            | invalid-account-id                              |
      | role_name                 | FailingCustodianRole                            |
      | role_path                 | /failing/                                       |
      | role_managed_policy_arns  | ["arn:aws:iam::aws:policy/InvalidPolicy"]      |
    When I run the task
    And the CloudFormation deployment fails due to invalid parameters
    Then the task should handle the error appropriately
    And relevant error information should be logged