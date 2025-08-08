Feature: Provision Product Task
  As a Service Catalog Puppet user
  I want to provision Service Catalog products
  So that I can deploy infrastructure as part of my orchestrated workflows

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And Service Catalog service is available

  Scenario: Provision product successfully for the first time
    Given a ProvisionProductTask with the following attributes:
      | attribute                                      | value                          |
      | manifest_file_path                            | /path/to/manifest.yaml         |
      | launch_name                                   | my-product-launch              |
      | region                                        | us-east-1                      |
      | account_id                                    | 123456789012                   |
      | portfolio                                     | my-portfolio                   |
      | product                                       | my-product                     |
      | version                                       | v1.0.0                         |
      | portfolio_get_all_products_and_their_versions_ref | products-ref-123          |
      | describe_provisioning_params_ref              | params-ref-456                 |
      | execution                                     | hub                            |
    And no previous provisioned product exists
    When I run the task
    Then a new provisioned product should be created
    And the task output should indicate provisioned: true
    And the task should complete successfully

  Scenario: Update existing provisioned product with changed parameters
    Given a ProvisionProductTask with the following attributes:
      | attribute                                      | value                          |
      | manifest_file_path                            | /path/to/manifest.yaml         |
      | launch_name                                   | existing-product-launch        |
      | region                                        | us-east-1                      |
      | account_id                                    | 123456789012                   |
      | portfolio                                     | my-portfolio                   |
      | product                                       | my-product                     |
      | version                                       | v1.0.0                         |
      | portfolio_get_all_products_and_their_versions_ref | products-ref-123          |
      | describe_provisioning_params_ref              | params-ref-456                 |
      | execution                                     | spoke                          |
    And launch parameters:
      | parameter_name    | parameter_value   |
      | InstanceType      | t3.large          |
      | Environment       | production        |
    And a previously provisioned product exists with different parameters
    When I run the task
    Then the existing provisioned product should be updated
    And the task output should indicate provisioned: true
    And the new parameters should be applied

  Scenario: Skip provisioning when parameters are unchanged
    Given a ProvisionProductTask with the following attributes:
      | attribute                                      | value                          |
      | manifest_file_path                            | /path/to/manifest.yaml         |
      | launch_name                                   | unchanged-product-launch       |
      | region                                        | us-west-2                      |
      | account_id                                    | 123456789012                   |
      | portfolio                                     | my-portfolio                   |
      | product                                       | my-product                     |
      | version                                       | v1.0.0                         |
      | portfolio_get_all_products_and_their_versions_ref | products-ref-123          |
      | describe_provisioning_params_ref              | params-ref-456                 |
      | execution                                     | hub                            |
    And launch parameters:
      | parameter_name    | parameter_value   |
      | InstanceType      | t3.medium         |
      | Environment       | development       |
    And a previously provisioned product exists with identical parameters and version
    When I run the task
    Then no provisioning should occur
    And the task output should indicate provisioned: false
    And the existing product should remain unchanged

  Scenario: Provision product with SSM parameter inputs
    Given a ProvisionProductTask with the following attributes:
      | attribute                                      | value                          |
      | manifest_file_path                            | /path/to/manifest.yaml         |
      | launch_name                                   | ssm-enabled-launch             |
      | region                                        | us-east-1                      |
      | account_id                                    | 123456789012                   |
      | portfolio                                     | my-portfolio                   |
      | product                                       | ssm-product                    |
      | version                                       | v2.0.0                         |
      | portfolio_get_all_products_and_their_versions_ref | products-ref-123          |
      | describe_provisioning_params_ref              | params-ref-456                 |
      | execution                                     | hub                            |
      | ssm_param_inputs                              | ["/myapp/database/endpoint", "/myapp/api/key"] |
    When I run the task
    Then the SSM parameters should be retrieved
    And the product should be provisioned with the SSM parameter values
    And the task should complete successfully

  Scenario: Handle clean up of tainted provisioned product
    Given a ProvisionProductTask with the following attributes:
      | attribute                                      | value                          |
      | manifest_file_path                            | /path/to/manifest.yaml         |
      | launch_name                                   | tainted-product-launch         |
      | region                                        | us-east-1                      |
      | account_id                                    | 123456789012                   |
      | portfolio                                     | my-portfolio                   |
      | product                                       | my-product                     |
      | version                                       | v1.0.0                         |
      | portfolio_get_all_products_and_their_versions_ref | products-ref-123          |
      | describe_provisioning_params_ref              | params-ref-456                 |
      | execution                                     | hub                            |
    And a previously provisioned product exists in TAINTED state
    When I run the task
    Then a warning should be logged about the tainted product
    And the product should be reprovisioned
    And the task should complete successfully

  Scenario: Provision product with custom priority and retry settings
    Given a ProvisionProductTask with the following attributes:
      | attribute                                      | value                          |
      | manifest_file_path                            | /path/to/manifest.yaml         |
      | launch_name                                   | priority-product-launch        |
      | region                                        | eu-west-1                      |
      | account_id                                    | 123456789012                   |
      | portfolio                                     | my-portfolio                   |
      | product                                       | my-product                     |
      | version                                       | v1.0.0                         |
      | portfolio_get_all_products_and_their_versions_ref | products-ref-123          |
      | describe_provisioning_params_ref              | params-ref-456                 |
      | execution                                     | spoke                          |
      | retry_count                                   | 3                              |
      | worker_timeout                                | 600                            |
      | requested_priority                            | 10                             |
    When I run the task
    Then the task should have priority 10
    And the task should be configured for 3 retries
    And the worker timeout should be 600 seconds
    And the product should be provisioned successfully