Feature: Terminate CloudFormation Stack Task
  As a Service Catalog Puppet user
  I want to safely terminate CloudFormation stacks in target accounts
  So that I can clean up infrastructure and manage stack lifecycles

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have CloudFormation delete permissions

  Scenario: Terminate existing CloudFormation stack successfully
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | my-infrastructure-stack      |
      | region       | us-east-1                    |
      | account_id   | 123456789012                 |
      | execution    | spoke                        |
    And the stack exists and is in a deletable state
    When I run the task
    Then the CloudFormation stack should be deleted
    And the stack deletion should complete successfully
    And an empty output file should be written

  Scenario: Attempt to terminate non-existent stack
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | non-existent-stack           |
      | region       | eu-west-1                    |
      | account_id   | 987654321098                 |
      | execution    | hub                          |
    And the stack does not exist
    When I run the task
    Then the task should handle the non-existent stack gracefully
    And no error should be raised for missing stack
    And an empty output file should be written

  Scenario: Terminate stack in different region
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | regional-test-stack          |
      | region       | ap-southeast-1               |
      | account_id   | 111122223333                 |
      | execution    | spoke                        |
    When I run the task
    Then the stack deletion should occur in the specified region
    And the regional CloudFormation client should be used
    And the stack should be terminated successfully

  Scenario: Terminate stack with dependencies
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | parent-infrastructure-stack  |
      | region       | us-west-2                    |
      | account_id   | 444455556666                 |
      | execution    | hub                          |
    And the stack has dependent resources or outputs referenced by other stacks
    When I run the task
    Then the task should attempt stack deletion
    And any dependency conflicts should be handled appropriately
    And proper error handling should occur if deletion fails due to dependencies

  Scenario: Terminate stack in cross-account scenario
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | cross-account-resources      |
      | region       | ca-central-1                 |
      | account_id   | 777788889999                 |
      | execution    | spoke                        |
    When I run the task
    Then the task should assume the appropriate cross-account role
    And the stack should be deleted in the target account
    And proper cross-account permissions should be validated
    And an empty output file should be written

  Scenario: Handle stack in DELETE_FAILED state
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | failed-deletion-stack        |
      | region       | eu-central-1                 |
      | account_id   | 888899990000                 |
      | execution    | hub                          |
    And the stack is currently in DELETE_FAILED state
    When I run the task
    Then the task should retry stack deletion
    And the ensure_deleted method should handle the failed state
    And the stack should eventually be cleaned up

  Scenario: Terminate stack with retain policy resources
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | retain-policy-stack          |
      | region       | us-east-2                    |
      | account_id   | 999000111222                 |
      | execution    | spoke                        |
    And the stack contains resources with DeletionPolicy: Retain
    When I run the task
    Then the stack should be deleted successfully
    And resources with retain policy should remain in the account
    And the stack metadata should be removed from CloudFormation

  Scenario: Handle termination with insufficient permissions
    Given a TerminateCloudFormationStackTask with the following attributes:
      | attribute    | value                        |
      | stack_name   | protected-stack              |
      | region       | ap-northeast-1               |
      | account_id   | 123123123123                 |
      | execution    | spoke                        |
    When I run the task
    And the execution role lacks cloudformation:DeleteStack permission
    Then the task should handle the permission error appropriately
    And relevant error information should be logged
    And the stack should remain unchanged