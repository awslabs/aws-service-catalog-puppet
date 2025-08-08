Feature: Generate Policies Task
  As a Service Catalog Puppet user
  I want to generate sharing policies for portfolios and event bus
  So that I can enable cross-account access and spoke execution mode

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And CloudFormation service is available

  Scenario: Generate policies successfully
    Given a GeneratePolicies task with the following attributes:
      | attribute                    | value                          |
      | account_id                  | 123456789012                   |
      | region                      | us-east-1                      |
      | organizations_to_share_with | []                             |
      | ous_to_share_with          | ["ou-example123", "ou-example456"] |
      | accounts_to_share_with     | ["987654321098", "111122223333"] |
    When I run the task
    Then a CloudFormation stack "servicecatalog-puppet-policies" should be created or updated
    And the stack should contain sharing policies for the specified OUs and accounts
    And an empty output file should be written
    And the task should complete successfully

  Scenario: Generate policies with organizations
    Given a GeneratePolicies task with the following attributes:
      | attribute                    | value                          |
      | account_id                  | 123456789012                   |
      | region                      | eu-west-1                      |
      | organizations_to_share_with | ["o-example12345"]             |
      | ous_to_share_with          | []                             |
      | accounts_to_share_with     | []                             |
    When I run the task
    Then a CloudFormation stack "servicecatalog-puppet-policies" should be created or updated
    And the stack should contain sharing policies for the specified organization
    And an empty output file should be written

  Scenario: Generate policies with too many accounts warning
    Given a GeneratePolicies task with the following attributes:
      | attribute                    | value                          |
      | account_id                  | 123456789012                   |
      | region                      | us-west-2                      |
      | organizations_to_share_with | []                             |
      | ous_to_share_with          | []                             |
      | accounts_to_share_with     | [list of 55 account IDs]      |
    When I run the task
    Then a warning should be logged about exceeding 50 accounts limit
    And the eventbus policy should not be created
    And spoke execution mode should not work
    And the task should still complete

  Scenario: Generate policies with SNS notifications
    Given a GeneratePolicies task with the following attributes:
      | attribute                    | value                          |
      | account_id                  | 123456789012                   |
      | region                      | us-east-1                      |
      | organizations_to_share_with | []                             |
      | ous_to_share_with          | ["ou-example123"]              |
      | accounts_to_share_with     | ["987654321098"]               |
    And SNS notifications are enabled
    When I run the task
    Then the CloudFormation stack should include SNS notification ARNs
    And an empty output file should be written