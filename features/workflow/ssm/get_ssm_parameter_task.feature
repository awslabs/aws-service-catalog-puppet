Feature: Get SSM Parameter Task
  As a Service Catalog Puppet user
  I want to retrieve AWS Systems Manager parameters from target accounts
  So that I can access configuration values and secrets for my deployments

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have SSM parameter read permissions

  Scenario: Get single SSM parameter successfully
    Given a GetSSMParameterTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 123456789012                    |
      | param_name       | /myapp/database/endpoint        |
      | jmespath_location|                                 |
      | region           | us-east-1                       |
    And the parameter exists in SSM
    When I run the task
    Then the SSM parameter should be retrieved successfully
    And the output should contain the parameter name as key
    And the output should contain the complete Parameter object with Value, Type, etc.
    And the task should complete successfully

  Scenario: Get SSM parameter with dynamic region replacement
    Given a GetSSMParameterTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 987654321098                    |
      | param_name       | /myapp/${AWS::Region}/config    |
      | jmespath_location|                                 |
      | region           | eu-west-1                       |
    When I run the task
    Then the parameter name should be resolved to "/myapp/eu-west-1/config"
    And the parameter should be retrieved using the resolved name
    And the output should use the resolved parameter name as key

  Scenario: Get SSM parameter with dynamic account ID replacement
    Given a GetSSMParameterTask with the following attributes:
      | attribute        | value                                     |
      | account_id       | 111122223333                              |
      | param_name       | /shared/${AWS::AccountId}/api-key         |
      | jmespath_location|                                           |
      | region           | ap-southeast-1                            |
    When I run the task
    Then the parameter name should be resolved to "/shared/111122223333/api-key"
    And the parameter should be retrieved using the resolved name
    And the output should contain the account-specific parameter

  Scenario: Get SSM parameter with JMESPath filtering
    Given a GetSSMParameterTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 444455556666                    |
      | param_name       | /myapp/config                   |
      | jmespath_location| database.host                   |
      | region           | us-west-2                       |
    And the parameter value is JSON: {"database": {"host": "db.example.com", "port": 5432}}
    When I run the task
    Then the parameter value should be parsed as JSON
    And the JMESPath expression should extract "db.example.com"
    And the output Parameter object should have the filtered value
    And the original parameter structure should be preserved with new Value

  Scenario: Handle non-existent SSM parameter gracefully
    Given a GetSSMParameterTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 777788889999                    |
      | param_name       | /nonexistent/parameter          |
      | jmespath_location|                                 |
      | region           | ca-central-1                    |
    And the parameter does not exist in SSM
    When I run the task
    Then the task should handle ParameterNotFound exception gracefully
    And the output should be an empty dictionary
    And no error should be raised
    And the task should complete successfully

  Scenario: Get SSM parameter with complex JMESPath expression
    Given a GetSSMParameterTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 888899990000                    |
      | param_name       | /myapp/services                 |
      | jmespath_location| services[?name=='api'].endpoint[0] |
      | region           | eu-central-1                    |
    And the parameter value is JSON with multiple services
    When I run the task
    Then the complex JMESPath expression should be evaluated
    And the specific service endpoint should be extracted
    And the filtered result should be set as the parameter value

  Scenario: Get parameters by path with pagination
    Given a GetSSMParameterByPathTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 999000111222                    |
      | path             | /myapp/                         |
      | jmespath_location|                                 |
      | region           | us-east-2                       |
    And multiple parameters exist under the path
    When I run the task
    Then all parameters under the path should be retrieved recursively
    And pagination should be used to handle large result sets
    And the output should contain all parameters with their full names as keys
    And each parameter should include the complete Parameter object

  Scenario: Get parameters by path with dynamic replacements
    Given a GetSSMParameterByPathTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 123123123123                    |
      | path             | /envs/${AWS::Region}/${AWS::AccountId}/ |
      | jmespath_location|                                 |
      | region           | ap-northeast-1                  |
    When I run the task
    Then the path should be resolved to "/envs/ap-northeast-1/123123123123/"
    And all parameters under the resolved path should be retrieved
    And the recursive search should find nested parameters

  Scenario: Get parameters by path with JMESPath filtering
    Given a GetSSMParameterByPathTask with the following attributes:
      | attribute        | value                           |
      | account_id       | 456456456456                    |
      | path             | /configs/                       |
      | jmespath_location| app.version                     |
      | region           | eu-west-2                       |
    And each parameter value is JSON with app configuration
    When I run the task
    Then each parameter value should be parsed as JSON
    And the JMESPath expression should be applied to each parameter
    And each parameter should have the filtered value extracted
    And the parameter structure should be preserved with new Values