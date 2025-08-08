Feature: Provision Stack Task
  As a Service Catalog Puppet user
  I want to provision CloudFormation stacks in target accounts
  So that I can deploy infrastructure using Infrastructure as Code

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have CloudFormation deployment permissions
    And the S3 template source is available

  Scenario: Provision new CloudFormation stack successfully
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | my-infrastructure-stack         |
      | region                 | us-east-1                       |
      | account_id             | 123456789012                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/infrastructure.yaml   |
      | version_id             | abc123def456                    |
      | launch_name            |                                 |
      | stack_set_name         |                                 |
      | get_s3_template_ref    | template-ref-123                |
      | capabilities           | ["CAPABILITY_IAM"]              |
      | use_service_role       | false                           |
      | execution              | spoke                           |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    And no stack with the same name exists
    When I run the task
    Then a new CloudFormation stack should be created
    And the stack should be provisioned with the specified template
    And the stack should use the provided parameters
    And the need_to_provision flag should be true
    And the task output should indicate successful provisioning

  Scenario: Update existing CloudFormation stack with template changes
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | existing-infrastructure-stack   |
      | region                 | eu-west-1                       |
      | account_id             | 987654321098                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/updated.yaml          |
      | version_id             | def456ghi789                    |
      | launch_name            |                                 |
      | stack_set_name         |                                 |
      | get_s3_template_ref    | template-ref-456                |
      | capabilities           | ["CAPABILITY_IAM"]              |
      | use_service_role       | false                           |
      | execution              | hub                             |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    And a stack with the same name exists in CREATE_COMPLETE status
    And the template content has changed
    When I run the task
    Then the existing stack should be updated
    And the need_to_provision flag should be true
    And the stack should reflect the new template changes
    And the task output should indicate successful update

  Scenario: Skip provisioning when stack and parameters are unchanged
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | unchanged-stack                 |
      | region                 | ap-southeast-1                  |
      | account_id             | 111122223333                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/same.yaml             |
      | version_id             | ghi789jkl012                    |
      | launch_name            |                                 |
      | stack_set_name         |                                 |
      | get_s3_template_ref    | template-ref-789                |
      | capabilities           | ["CAPABILITY_IAM"]              |
      | use_service_role       | false                           |
      | execution              | spoke                           |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    And a stack with the same name exists in CREATE_COMPLETE status
    And the template content is identical
    And the parameters are identical
    When I run the task
    Then no provisioning should occur
    And the need_to_provision flag should be false
    And the task should complete without CloudFormation operations
    And the task output should indicate no provisioning was needed

  Scenario: Provision stack with Service Catalog launch name resolution
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | fallback-stack-name             |
      | region                 | us-west-2                       |
      | account_id             | 444455556666                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/sc-product.yaml       |
      | version_id             | jkl012mno345                    |
      | launch_name            | my-service-catalog-product      |
      | stack_set_name         |                                 |
      | get_s3_template_ref    | template-ref-012                |
      | capabilities           | ["CAPABILITY_IAM"]              |
      | use_service_role       | false                           |
      | execution              | spoke                           |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    And a Service Catalog provisioned product exists with the launch name
    When I run the task
    Then the stack name should be resolved from the provisioned product
    And the actual CloudFormation stack should be identified
    And the stack should be managed using the resolved stack name

  Scenario: Provision stack with StackSet name resolution
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | fallback-stack-name             |
      | region                 | ca-central-1                    |
      | account_id             | 777788889999                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/stackset.yaml         |
      | version_id             | mno345pqr678                    |
      | launch_name            |                                 |
      | stack_set_name         | MyOrganizationalStackSet        |
      | get_s3_template_ref    | template-ref-345                |
      | capabilities           | ["CAPABILITY_IAM"]              |
      | use_service_role       | false                           |
      | execution              | spoke                           |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    And a StackSet instance exists in the account
    When I run the task
    Then the stack name should be resolved from the StackSet instance
    And the StackSet-managed stack should be identified
    And the stack should be managed appropriately for StackSet deployment

  Scenario: Handle stack in ROLLBACK_COMPLETE status with deletion enabled
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | failed-stack                    |
      | region                 | eu-central-1                    |
      | account_id             | 888899990000                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/retry.yaml            |
      | version_id             | pqr678stu901                    |
      | launch_name            |                                 |
      | stack_set_name         |                                 |
      | get_s3_template_ref    | template-ref-678                |
      | capabilities           | ["CAPABILITY_IAM"]              |
      | use_service_role       | false                           |
      | execution              | spoke                           |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    And a stack exists in ROLLBACK_COMPLETE status
    And deletion of rollback complete stacks is enabled
    When I run the task
    Then the failed stack should be deleted first
    And a new stack should be created with the same name
    And the provisioning should succeed

  Scenario: Provision stack with service role
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | service-role-stack              |
      | region                 | us-east-2                       |
      | account_id             | 999000111222                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/service-role.yaml     |
      | version_id             | stu901vwx234                    |
      | launch_name            |                                 |
      | stack_set_name         |                                 |
      | get_s3_template_ref    | template-ref-901                |
      | capabilities           | ["CAPABILITY_NAMED_IAM"]        |
      | use_service_role       | true                            |
      | execution              | spoke                           |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    When I run the task
    Then the stack should be deployed using the service role ARN
    And the service role should be used for CloudFormation operations
    And the stack deployment should respect the service role permissions

  Scenario: Provision stack with custom tags
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                                                      |
      | stack_name             | tagged-stack                                               |
      | region                 | ap-northeast-1                                             |
      | account_id             | 123123123123                                               |
      | bucket                 | my-template-bucket                                         |
      | key                    | templates/tagged.yaml                                      |
      | version_id             | vwx234yzb567                                               |
      | launch_name            |                                                            |
      | stack_set_name         |                                                            |
      | get_s3_template_ref    | template-ref-234                                           |
      | capabilities           | ["CAPABILITY_IAM"]                                         |
      | use_service_role       | false                                                      |
      | execution              | hub                                                        |
      | manifest_file_path     | /path/to/manifest.yaml                                     |
      | tags                   | [{"key": "Environment", "value": "Production"}]           |
    When I run the task
    Then the stack should be created with the specified tags
    And the custom tags should be applied in addition to standard framework tags
    And the tags should be visible in the CloudFormation console

  Scenario: Handle stack provisioning failure
    Given a ProvisionStackTask with the following attributes:
      | attribute              | value                           |
      | stack_name             | failing-stack                   |
      | region                 | us-west-1                       |
      | account_id             | 456456456456                    |
      | bucket                 | my-template-bucket              |
      | key                    | templates/invalid.yaml          |
      | version_id             | yzb567cde890                    |
      | launch_name            |                                 |
      | stack_set_name         |                                 |
      | get_s3_template_ref    | template-ref-567                |
      | capabilities           | ["CAPABILITY_IAM"]              |
      | use_service_role       | false                           |
      | execution              | spoke                           |
      | manifest_file_path     | /path/to/manifest.yaml          |
      | tags                   | []                              |
    When I run the task
    And the CloudFormation template contains errors
    Then the task should handle the provisioning failure appropriately
    And detailed error information should be logged
    And the exception should include the provisioning parameters for debugging