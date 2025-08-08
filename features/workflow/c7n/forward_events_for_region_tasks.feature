Feature: Forward Events For Region Task
  As a Service Catalog Puppet user
  I want to create EventBridge rules that forward regional events to the Cloud Custodian hub account
  So that Cloud Custodian can monitor and act on events across all regions and accounts

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have CloudFormation deployment capabilities
    And the Cloud Custodian event forwarder role exists

  Scenario: Create regional event forwarding rule successfully
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 123456789012    |
      | custodian_region | us-east-1       |
    When I run the task
    Then a CloudFormation stack should be created with name "servicecatalog-puppet-c7n-eventforwarding-region"
    And an EventBridge rule "ForwardAll" should be created
    And the rule should be enabled and forward all events from the current account
    And the rule should target the custodian event bus in the hub account
    And the rule should use the c7nEventForwarder role for cross-account access
    And an empty output file should be written

  Scenario: Create event forwarding for different custodian region
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 987654321098    |
      | custodian_region | eu-west-1       |
    When I run the task
    Then the EventBridge rule target should point to the eu-west-1 event bus
    And the event bus ARN should include the correct custodian account and region
    And the rule should be created with proper partition awareness
    And the CloudFormation stack should deploy successfully

  Scenario: Create event forwarding rule with account filtering
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 111122223333    |
      | custodian_region | ap-southeast-1  |
    And the current account ID is "555666777888"
    When I run the task
    Then the EventBridge rule should have an event pattern filtering for account "555666777888"
    And only events from the current account should be forwarded
    And the rule description should indicate it forwards events for c7n

  Scenario: Update existing regional event forwarding configuration
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 444455556666    |
      | custodian_region | ca-central-1    |
    And a CloudFormation stack already exists with the same name
    When I run the task
    Then the existing stack should be updated instead of created
    And the event rule should be updated to target the new configuration
    And change sets should not be used for the update
    And an empty output file should be written

  Scenario: Create event forwarding with SNS notifications
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 777788889999    |
      | custodian_region | us-west-2       |
    And SNS notifications are enabled
    When I run the task
    Then the CloudFormation stack should include notification ARNs
    And notifications should be sent to the regional events topic
    And the stack should complete successfully
    And the event forwarding rule should be active

  Scenario: Handle multiple partition support for event forwarding
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 888899990000    |
      | custodian_region | us-gov-west-1   |
    When I run the task in AWS GovCloud partition
    Then the event bus target ARN should use the correct partition
    And the forwarder role ARN should use the correct partition
    And the CloudFormation template should handle partition references correctly

  Scenario: Verify event rule configuration
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value           |
      | c7n_account_id   | 999000111222    |
      | custodian_region | eu-central-1    |
    When I run the task
    Then the EventBridge rule should have exactly one target
    And the target ID should be "CloudCustodianHubEventBusArn"
    And the target should reference the c7nEventForwarder role
    And the rule state should be "ENABLED"

  Scenario: Handle regional event forwarding setup failure
    Given a ForwardEventsForRegionTask with the following attributes:
      | attribute        | value              |
      | c7n_account_id   | invalid-account-id |
      | custodian_region | invalid-region     |
    When I run the task
    And the CloudFormation deployment fails due to invalid parameters
    Then the task should handle the error appropriately
    And relevant error information should be logged