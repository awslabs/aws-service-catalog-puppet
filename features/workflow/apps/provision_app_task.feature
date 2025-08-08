Feature: Provision App Task
  As a Service Catalog Puppet user
  I want to provision applications in target accounts
  So that I can deploy applications as part of my infrastructure management pipeline

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And the S3 bucket contains the application artifacts

  Scenario: Provision app successfully
    Given a ProvisionAppTask with the following attributes:
      | attribute              | value                     |
      | app_name              | my-application            |
      | region                | us-east-1                 |
      | account_id            | 123456789012              |
      | bucket                | my-deployment-bucket      |
      | key                   | apps/my-app/v1.0.0.zip   |
      | version_id            | abc123def456              |
      | execution             | hub                       |
    When I run the task
    Then the app should be provisioned in the target account
    And an empty output file should be written
    And the task should complete successfully

  Scenario: Provision app with launch parameters
    Given a ProvisionAppTask with the following attributes:
      | attribute              | value                     |
      | app_name              | parameterized-app         |
      | region                | eu-west-1                 |
      | account_id            | 987654321098              |
      | bucket                | my-deployment-bucket      |
      | key                   | apps/param-app/v2.1.0.zip|
      | version_id            | xyz789abc123              |
      | execution             | spoke                     |
    And launch parameters:
      | parameter_name    | parameter_value   |
      | InstanceType      | t3.medium         |
      | Environment       | production        |
    When I run the task
    Then the app should be provisioned with the specified parameters
    And an empty output file should be written

  Scenario: Provision app with SSM parameter inputs
    Given a ProvisionAppTask with the following attributes:
      | attribute              | value                     |
      | app_name              | ssm-enabled-app           |
      | region                | us-west-2                 |
      | account_id            | 111122223333              |
      | bucket                | my-deployment-bucket      |
      | key                   | apps/ssm-app/v1.5.0.zip  |
      | version_id            | def456ghi789              |
      | execution             | hub                       |
    And SSM parameter inputs:
      | ssm_param_name               |
      | /myapp/database/endpoint     |
      | /myapp/api/key               |
    When I run the task
    Then the SSM parameters should be retrieved and used
    And the app should be provisioned successfully
    And an empty output file should be written

  Scenario: Handle provisioning failure
    Given a ProvisionAppTask with the following attributes:
      | attribute              | value                     |
      | app_name              | failing-app               |
      | region                | ap-southeast-1            |
      | account_id            | 444455556666              |
      | bucket                | non-existent-bucket       |
      | key                   | apps/missing/app.zip      |
      | version_id            | invalid-version           |
      | execution             | hub                       |
    When I run the task
    And the S3 object cannot be found
    Then the task should handle the error appropriately
    And relevant error information should be logged

  Scenario: Provision app with retry configuration
    Given a ProvisionAppTask with the following attributes:
      | attribute              | value                     |
      | app_name              | retry-app                 |
      | region                | ca-central-1              |
      | account_id            | 777788889999              |
      | bucket                | my-deployment-bucket      |
      | key                   | apps/retry-app/v1.0.0.zip|
      | version_id            | ghi789jkl012              |
      | execution             | spoke                     |
      | retry_count           | 3                         |
      | worker_timeout        | 300                       |
    When I run the task
    Then the task should be configured for 3 retries
    And the worker timeout should be 300 seconds
    And the app should be provisioned successfully