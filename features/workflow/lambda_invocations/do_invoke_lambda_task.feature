Feature: Do Invoke Lambda Task
  As a Service Catalog Puppet user
  I want to invoke AWS Lambda functions as part of my deployment pipeline
  So that I can execute custom business logic and integrations during infrastructure deployments

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have Lambda invoke permissions
    And the specified Lambda function exists

  Scenario: Invoke Lambda function with RequestResponse invocation type
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | data-processing-function        |
      | region                   | us-east-1                       |
      | account_id               | 123456789012                    |
      | function_name            | my-data-processor               |
      | qualifier                | $LATEST                         |
      | invocation_type          | RequestResponse                 |
      | manifest_file_path       | /path/to/manifest.yaml          |
    When I run the task
    Then the Lambda function should be invoked synchronously
    And the payload should include account_id, region, and parameters
    And the response status code should be 200
    And an empty output file should be written if successful

  Scenario: Invoke Lambda function with Event invocation type
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | async-processing-function       |
      | region                   | eu-west-1                       |
      | account_id               | 987654321098                    |
      | function_name            | my-async-processor              |
      | qualifier                | PROD                            |
      | invocation_type          | Event                           |
      | manifest_file_path       | /path/to/manifest.yaml          |
    When I run the task
    Then the Lambda function should be invoked asynchronously
    And the response status code should be 202
    And the task should complete without waiting for function completion
    And an empty output file should be written

  Scenario: Invoke Lambda function with DryRun invocation type
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | validation-function             |
      | region                   | ap-southeast-1                  |
      | account_id               | 111122223333                    |
      | function_name            | my-validator                    |
      | qualifier                | v2.0                            |
      | invocation_type          | DryRun                          |
      | manifest_file_path       | /path/to/manifest.yaml          |
    When I run the task
    Then the Lambda function should validate the payload without executing
    And the response status code should be 204
    And no actual processing should occur in the Lambda function
    And an empty output file should be written

  Scenario: Invoke Lambda function with custom parameters
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | custom-integration-function     |
      | region                   | us-west-2                       |
      | account_id               | 444455556666                    |
      | function_name            | my-custom-integration           |
      | qualifier                | $LATEST                         |
      | invocation_type          | RequestResponse                 |
      | manifest_file_path       | /path/to/manifest.yaml          |
    And the task has custom parameter values
    When I run the task
    Then the Lambda payload should include the custom parameters
    And the parameters should be properly serialized in the payload
    And the Lambda function should receive all necessary context data

  Scenario: Handle Lambda function execution error
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | error-prone-function            |
      | region                   | ca-central-1                    |
      | account_id               | 777788889999                    |
      | function_name            | my-error-function               |
      | qualifier                | $LATEST                         |
      | invocation_type          | RequestResponse                 |
      | manifest_file_path       | /path/to/manifest.yaml          |
    When I run the task
    And the Lambda function returns a FunctionError
    Then an exception should be raised with the error payload
    And the error details should be properly reported
    And the task should fail with appropriate error information

  Scenario: Handle Lambda invocation failure with wrong status code
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | failing-invocation              |
      | region                   | eu-central-1                    |
      | account_id               | 888899990000                    |
      | function_name            | my-function                     |
      | qualifier                | $LATEST                         |
      | invocation_type          | RequestResponse                 |
      | manifest_file_path       | /path/to/manifest.yaml          |
    When I run the task
    And the Lambda service returns an unexpected status code
    Then an exception should be raised indicating invocation failure
    And the exception should include the lambda invocation name, account, and region

  Scenario: Invoke Lambda function in hub account home region
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | hub-region-function             |
      | region                   | us-east-1                       |
      | account_id               | 999000111222                    |
      | function_name            | central-orchestrator            |
      | qualifier                | $LATEST                         |
      | invocation_type          | Event                           |
      | manifest_file_path       | /path/to/manifest.yaml          |
    When I run the task
    Then the Lambda function should be invoked from the hub account home region
    And the hub regional client should be used for the invocation
    And the cross-region invocation should complete successfully

  Scenario: Invoke Lambda function with specific version qualifier
    Given a DoInvokeLambdaTask with the following attributes:
      | attribute                | value                           |
      | lambda_invocation_name   | versioned-function              |
      | region                   | ap-northeast-1                  |
      | account_id               | 123123123123                    |
      | function_name            | my-versioned-function           |
      | qualifier                | 15                              |
      | invocation_type          | RequestResponse                 |
      | manifest_file_path       | /path/to/manifest.yaml          |
    When I run the task
    Then the specific version "15" of the Lambda function should be invoked
    And the qualifier should be included in the invocation request
    And the versioned function logic should be executed