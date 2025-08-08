Feature: Terminate Stack Task
  As a Service Catalog Puppet user
  I want to terminate CloudFormation stacks
  So that I can clean up infrastructure when it's no longer needed

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And CloudFormation service is available

  Scenario: Terminate stack successfully
    Given a TerminateStackTask with the following attributes:
      | attribute              | value                     |
      | stack_name            | my-infrastructure-stack   |
      | region                | us-east-1                 |
      | account_id            | 123456789012              |
      | bucket                | my-template-bucket        |
      | key                   | templates/infra-v1.yaml   |
      | version_id            | abc123def456              |
      | launch_name           | infra-launch-001          |
      | stack_set_name        |                           |
      | use_service_role      | false                     |
      | execution             | hub                       |
    And capabilities:
      | capability            |
      | CAPABILITY_IAM        |
      | CAPABILITY_NAMED_IAM  |
    And an existing CloudFormation stack exists
    When I run the task
    Then the CloudFormation stack should be terminated
    And the stack deletion should complete successfully
    And an empty output file should be written

  Scenario: Terminate stack with service role
    Given a TerminateStackTask with the following attributes:
      | attribute              | value                     |
      | stack_name            | service-role-stack        |
      | region                | us-west-2                 |
      | account_id            | 987654321098              |
      | bucket                | template-artifacts        |
      | key                   | stacks/service-stack.yaml |
      | version_id            | xyz789abc123              |
      | launch_name           | service-launch-002        |
      | stack_set_name        |                           |
      | use_service_role      | true                      |
      | execution             | spoke                     |
    And capabilities:
      | capability            |
      | CAPABILITY_IAM        |
    And a CloudFormation service role is configured
    When I run the task
    Then the stack should be terminated using the service role
    And proper IAM permissions should be used for termination
    And the task should complete successfully

  Scenario: Terminate stack with SSM parameter inputs
    Given a TerminateStackTask with the following attributes:
      | attribute              | value                     |
      | stack_name            | parameterized-stack       |
      | region                | eu-central-1              |
      | account_id            | 111122223333              |
      | bucket                | cfn-templates             |
      | key                   | templates/param-stack.yaml|
      | version_id            | def456ghi789              |
      | launch_name           | param-launch-003          |
      | stack_set_name        |                           |
      | use_service_role      | false                     |
      | execution             | hub                       |
      | ssm_param_inputs      | ["/app/database/endpoint", "/app/cache/cluster"] |
    When I run the task
    Then the SSM parameters should be retrieved for context
    And the stack should be terminated appropriately
    And SSM parameter values should be logged for reference

  Scenario: Terminate stack set instance
    Given a TerminateStackTask with the following attributes:
      | attribute              | value                     |
      | stack_name            | stack-set-instance        |
      | region                | ap-southeast-1            |
      | account_id            | 444455556666              |
      | bucket                | stackset-templates        |
      | key                   | stacksets/multi-account.yaml |
      | version_id            | ghi789jkl012              |
      | launch_name           | stackset-launch-004       |
      | stack_set_name        | multi-account-stackset    |
      | use_service_role      | true                      |
      | execution             | hub                       |
    And capabilities:
      | capability            |
      | CAPABILITY_IAM        |
      | CAPABILITY_NAMED_IAM  |
    And a StackSet instance exists in the target account
    When I run the task
    Then the StackSet instance should be removed from the target account
    And the StackSet operation should complete successfully
    And the task should handle StackSet-specific termination logic

  Scenario: Handle termination when stack does not exist
    Given a TerminateStackTask with the following attributes:
      | attribute              | value                     |
      | stack_name            | non-existent-stack        |
      | region                | ca-central-1              |
      | account_id            | 777788889999              |
      | bucket                | template-bucket           |
      | key                   | templates/missing.yaml    |
      | version_id            | jkl012mno345              |
      | launch_name           | missing-launch-005        |
      | stack_set_name        |                           |
      | use_service_role      | false                     |
      | execution             | spoke                     |
    And no stack exists with the specified name
    When I run the task
    Then the task should handle the missing stack gracefully
    And appropriate logging should indicate stack was not found
    And the task should complete successfully without error

  Scenario: Terminate stack with custom retry and timeout settings
    Given a TerminateStackTask with the following attributes:
      | attribute              | value                     |
      | stack_name            | retry-stack               |
      | region                | us-east-1                 |
      | account_id            | 888899990000              |
      | bucket                | infrastructure-templates  |
      | key                   | stacks/complex-stack.yaml |
      | version_id            | mno345pqr678              |
      | launch_name           | complex-launch-006        |
      | stack_set_name        |                           |
      | use_service_role      | false                     |
      | execution             | hub                       |
      | retry_count           | 5                         |
      | worker_timeout        | 1800                      |
      | requested_priority    | 15                        |
    And capabilities:
      | capability            |
      | CAPABILITY_NAMED_IAM  |
    When I run the task
    Then the task should have priority 15
    And the task should be configured for 5 retries
    And the worker timeout should be 1800 seconds
    And the stack termination should proceed with these settings

  Scenario: Terminate stack with launch and manifest parameters
    Given a TerminateStackTask with the following attributes:
      | attribute              | value                     |
      | stack_name            | configured-stack          |
      | region                | us-west-1                 |
      | account_id            | 123456789012              |
      | bucket                | config-templates          |
      | key                   | stacks/config-stack.yaml  |
      | version_id            | pqr678stu901              |
      | launch_name           | config-launch-007         |
      | stack_set_name        |                           |
      | use_service_role      | false                     |
      | execution             | spoke                     |
    And launch parameters:
      | parameter_name    | parameter_value   |
      | Environment      | production        |
      | InstanceType     | t3.large          |
    And manifest parameters:
      | parameter_name    | parameter_value   |
      | Region           | us-west-1         |
      | Application      | MyApp             |
    And account parameters:
      | parameter_name    | parameter_value   |
      | VpcId            | vpc-12345678      |
    When I run the task
    Then the stack should be terminated with all parameter context
    And parameter values should be logged for reference
    And the termination should complete successfully