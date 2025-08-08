Feature: Do Execute Code Build Run Task
  As a Service Catalog Puppet user
  I want to execute CodeBuild runs in target accounts
  So that I can perform custom operations as part of my deployment pipeline

  Background:
    Given I have a CodeBuild project configured
    And the project has environment variables defined
    And I have the necessary AWS permissions

  Scenario: Execute CodeBuild run successfully
    Given a DoExecuteCodeBuildRunTask with the following attributes:
      | attribute             | value                    |
      | code_build_run_name   | my-codebuild-run        |
      | region               | us-east-1                |
      | account_id           | 123456789012             |
      | project_name         | my-project               |
      | manifest_file_path   | /path/to/manifest.yaml   |
    When I run the task
    Then the CodeBuild project should be executed with environment variables
    And the TARGET_ACCOUNT_ID should be set to "123456789012"
    And the TARGET_REGION should be set to "us-east-1"
    And the build should complete successfully
    And an empty output file should be written

  Scenario: Execute CodeBuild run with parameters
    Given a DoExecuteCodeBuildRunTask with the following attributes:
      | attribute             | value                    |
      | code_build_run_name   | parameterized-run       |
      | region               | eu-west-1                |
      | account_id           | 987654321098             |
      | project_name         | param-project            |
      | manifest_file_path   | /path/to/manifest.yaml   |
    And the project has environment variables:
      | name          | type      |
      | CUSTOM_PARAM  | PLAINTEXT |
      | OTHER_PARAM   | PLAINTEXT |
    And I have parameter values:
      | CUSTOM_PARAM | custom-value |
      | OTHER_PARAM  | other-value  |
    When I run the task
    Then the CodeBuild project should be executed with the custom parameters
    And the build should complete successfully

  Scenario: Handle CodeBuild execution failure
    Given a DoExecuteCodeBuildRunTask with the following attributes:
      | attribute             | value                    |
      | code_build_run_name   | failing-run             |
      | region               | us-west-2                |
      | account_id           | 111122223333             |
      | project_name         | failing-project          |
      | manifest_file_path   | /path/to/manifest.yaml   |
    When I run the task
    And the CodeBuild execution fails
    Then an exception should be raised with message "Executing CodeBuild failed"