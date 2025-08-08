Feature: Do Terminate Product Task
  As a Service Catalog Puppet user
  I want to terminate Service Catalog provisioned products
  So that I can clean up resources when they are no longer needed

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And Service Catalog service is available

  Scenario: Terminate existing provisioned product successfully
    Given a DoTerminateProductTask with the following attributes:
      | attribute              | value                     |
      | launch_name           | my-product-launch         |
      | region                | us-east-1                 |
      | account_id            | 123456789012              |
      | portfolio             | my-portfolio              |
      | product               | my-product                |
      | version               | v1.0.0                    |
      | execution             | hub                       |
    And a provisioned product exists with the specified launch name
    When I run the task
    Then the provisioned product should be terminated
    And the termination should complete successfully
    And an empty output file should be written

  Scenario: Handle termination when product does not exist
    Given a DoTerminateProductTask with the following attributes:
      | attribute              | value                     |
      | launch_name           | non-existent-launch       |
      | region                | us-west-2                 |
      | account_id            | 123456789012              |
      | portfolio             | my-portfolio              |
      | product               | my-product                |
      | version               | v1.0.0                    |
      | execution             | spoke                     |
    And no provisioned product exists with the specified launch name
    When I run the task
    Then a ResourceNotFoundException should be handled gracefully
    And the task should log that the product was not found
    And an empty output file should be written
    And the task should complete successfully

  Scenario: Terminate product with custom retry and timeout settings
    Given a DoTerminateProductTask with the following attributes:
      | attribute              | value                     |
      | launch_name           | retry-product-launch      |
      | region                | eu-central-1              |
      | account_id            | 987654321098              |
      | portfolio             | my-portfolio              |
      | product               | my-product                |
      | version               | v2.0.0                    |
      | execution             | hub                       |
      | retry_count           | 3                         |
      | worker_timeout        | 900                       |
    And a provisioned product exists with the specified launch name
    When I run the task
    Then the task should be configured for 3 retries
    And the worker timeout should be 900 seconds
    And the provisioned product should be terminated

  Scenario: Terminate product with launch parameters and SSM inputs
    Given a DoTerminateProductTask with the following attributes:
      | attribute              | value                     |
      | launch_name           | parameterized-launch      |
      | region                | us-east-1                 |
      | account_id            | 123456789012              |
      | portfolio             | my-portfolio              |
      | product               | my-product                |
      | version               | v1.5.0                    |
      | execution             | spoke                     |
      | ssm_param_inputs      | ["/myapp/config/param"]   |
    And launch parameters:
      | parameter_name    | parameter_value   |
      | InstanceType      | t3.medium         |
      | Environment       | development       |
    And manifest parameters:
      | parameter_name    | parameter_value   |
      | Region           | us-east-1          |
    And a provisioned product exists with the specified launch name
    When I run the task
    Then the provisioned product should be terminated
    And the task should complete with all parameters logged

  Scenario: Wait for termination to complete when product is under change
    Given a DoTerminateProductTask with the following attributes:
      | attribute              | value                     |
      | launch_name           | changing-product-launch   |
      | region                | ap-southeast-2            |
      | account_id            | 111122223333              |
      | portfolio             | my-portfolio              |
      | product               | my-product                |
      | version               | v1.0.0                    |
      | execution             | hub                       |
    And a provisioned product exists that is currently under change
    When I run the task
    Then the task should wait for the current operation to complete
    And then proceed with termination
    And the termination should complete successfully