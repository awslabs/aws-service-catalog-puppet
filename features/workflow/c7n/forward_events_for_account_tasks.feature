Feature: Forward Events For Account Task
  As a Service Catalog Puppet user
  I want to set up event forwarding from spoke accounts to the Cloud Custodian hub account
  So that Cloud Custodian can receive and process events from all monitored accounts

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have CloudFormation deployment capabilities
    And the Cloud Custodian hub account is configured

  Scenario: Create event forwarding role successfully
    Given a ForwardEventsForAccountTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 123456789012    |
      | custodian_region | us-east-1       |
    When I run the task
    Then a CloudFormation stack should be created with name "servicecatalog-puppet-c7n-eventforwarding"
    And an IAM role "c7nEventForwarder" should be created
    And the role should have path "/servicecatalog-puppet/c7n/"
    And the role should allow events:PutEvents to the custodian region event bus
    And the role should allow Amazon EventBridge to assume it
    And an empty output file should be written

  Scenario: Create event forwarding for different custodian region
    Given a ForwardEventsForAccountTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 987654321098    |
      | custodian_region | eu-west-1       |
    When I run the task
    Then the IAM policy should target the eu-west-1 event bus
    And the event bus ARN should include the correct custodian account and region
    And the role should be created with proper permissions
    And the CloudFormation stack should deploy successfully

  Scenario: Update existing event forwarding configuration
    Given a ForwardEventsForAccountTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 111122223333    |
      | custodian_region | ap-southeast-1  |
    And a CloudFormation stack already exists with the same name
    When I run the task
    Then the existing stack should be updated instead of created
    And the role permissions should be updated to target the new configuration
    And change sets should not be used for the update
    And an empty output file should be written

  Scenario: Create event forwarding with SNS notifications
    Given a ForwardEventsForAccountTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 444455556666    |
      | custodian_region | ca-central-1    |
    And SNS notifications are enabled
    When I run the task
    Then the CloudFormation stack should include notification ARNs
    And notifications should be sent to the regional events topic
    And the stack should complete successfully
    And the event forwarding role should be functional

  Scenario: Handle multiple partition support
    Given a ForwardEventsForAccountTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 777788889999    |
      | custodian_region | us-gov-west-1   |
    When I run the task in AWS GovCloud partition
    Then the event bus ARN should use the correct partition
    And the role should be created with partition-aware permissions
    And the CloudFormation template should handle partition references correctly

  Scenario: Handle event forwarding setup failure
    Given a ForwardEventsForAccountTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | invalid-account |
      | custodian_region | invalid-region  |
    When I run the task
    And the CloudFormation deployment fails due to invalid parameters
    Then the task should handle the error appropriately
    And relevant error information should be logged

  Scenario: Verify event forwarding role permissions
    Given a ForwardEventsForAccountTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 888899990000    |
      | custodian_region | us-west-2       |
    When I run the task
    Then the role should have exactly one inline policy named "AllowPutEvents"
    And the policy should allow only events:PutEvents action
    And the resource should be the specific event bus in the custodian account and region
    And the assume role policy should allow only events.amazonaws.com service