Feature: Do Execute Service Control Policies Task
  As a Service Catalog Puppet user
  I want to execute and attach service control policies
  So that I can enforce governance and compliance across AWS accounts and organizational units

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And AWS Organizations service is available
    And service control policies are enabled in the organization

  Scenario: Execute service control policy for an account successfully
    Given a DoExecuteServiceControlPoliciesTask with the following attributes:
      | attribute                    | value                          |
      | service_control_policy_name  | restrict-regions-policy        |
      | region                      | us-east-1                      |
      | account_id                  | 123456789012                   |
      | ou_name                     |                                |
      | get_or_create_policy_ref    | scp-policy-ref-123             |
      | description                 | Restrict access to specific regions |
      | requested_priority          | 5                              |
      | manifest_file_path          | /path/to/manifest.yaml         |
    And content:
      | policy_section    | policy_value                   |
      | Version          | 2012-10-17                     |
      | Statement        | [deny ec2:* for non-approved regions] |
    When I run the task
    Then the service control policy should be attached to the specified account
    And the policy should enforce the defined restrictions
    And the task should complete successfully

  Scenario: Execute service control policy for an organizational unit
    Given a DoExecuteServiceControlPoliciesTask with the following attributes:
      | attribute                    | value                          |
      | service_control_policy_name  | security-baseline-policy       |
      | region                      | us-west-2                      |
      | account_id                  |                                |
      | ou_name                     | Security-OU                    |
      | get_or_create_policy_ref    | scp-policy-ref-456             |
      | description                 | Security baseline for all accounts |
      | requested_priority          | 10                             |
      | manifest_file_path          | /path/to/manifest.yaml         |
    And content:
      | policy_section    | policy_value                   |
      | Version          | 2012-10-17                     |
      | Statement        | [deny dangerous actions]       |
    When I run the task
    Then the service control policy should be attached to the specified organizational unit
    And all accounts in the OU should inherit the policy restrictions
    And the task should complete successfully

  Scenario: Execute service control policy with high priority
    Given a DoExecuteServiceControlPoliciesTask with the following attributes:
      | attribute                    | value                          |
      | service_control_policy_name  | critical-security-policy       |
      | region                      | eu-central-1                   |
      | account_id                  | 987654321098                   |
      | ou_name                     |                                |
      | get_or_create_policy_ref    | scp-policy-ref-789             |
      | description                 | Critical security restrictions |
      | requested_priority          | 1                              |
      | manifest_file_path          | /path/to/manifest.yaml         |
    And content:
      | policy_section    | policy_value                   |
      | Version          | 2012-10-17                     |
      | Statement        | [deny root access]             |
    When I run the task
    Then the task should be executed with priority 1
    And the service control policy should be attached to the account
    And critical security restrictions should be enforced

  Scenario: Execute service control policy with complex JSON content
    Given a DoExecuteServiceControlPoliciesTask with the following attributes:
      | attribute                    | value                          |
      | service_control_policy_name  | multi-condition-policy         |
      | region                      | ap-southeast-2                 |
      | account_id                  | 111122223333                   |
      | ou_name                     |                                |
      | get_or_create_policy_ref    | scp-policy-ref-012             |
      | description                 | Policy with multiple conditions |
      | requested_priority          | 5                              |
      | manifest_file_path          | /path/to/manifest.yaml         |
    And complex content with multiple statements and conditions
    When I run the task
    Then the complex policy content should be processed correctly
    And the service control policy should be attached with all conditions
    And the task should complete successfully

  Scenario: Handle organizational unit lookup by name
    Given a DoExecuteServiceControlPoliciesTask with the following attributes:
      | attribute                    | value                          |
      | service_control_policy_name  | development-restrictions       |
      | region                      | ca-central-1                   |
      | account_id                  |                                |
      | ou_name                     | Development                    |
      | get_or_create_policy_ref    | scp-policy-ref-345             |
      | description                 | Development environment restrictions |
      | requested_priority          | 8                              |
      | manifest_file_path          | /path/to/manifest.yaml         |
    And content:
      | policy_section    | policy_value                   |
      | Version          | 2012-10-17                     |
      | Statement        | [allow development actions only] |
    When I run the task
    Then the organizational unit should be found by name "Development"
    And the service control policy should be attached to that organizational unit
    And development-specific restrictions should be applied