Feature: Get S3 Object Task
  As a Service Catalog Puppet user
  I want to retrieve objects from S3 buckets
  So that I can access configuration files, templates, and other artifacts during workflow execution

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And S3 service is available

  Scenario: Get S3 object successfully
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 123456789012              |
      | key                   | config/application.json   |
      | region                | us-east-1                 |
    And the S3 bucket "sc-puppet-parameters-123456789012" exists
    And the object "config/application.json" exists in the bucket
    When I run the task
    Then the S3 object should be retrieved successfully
    And the object content should be written to output without JSON encoding
    And the task should complete successfully

  Scenario: Get S3 object with nested key path
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 987654321098              |
      | key                   | environments/prod/database/config.yaml |
      | region                | us-west-2                 |
    And the S3 bucket "sc-puppet-parameters-987654321098" exists
    And the object with nested path exists in the bucket
    When I run the task
    Then the S3 object should be retrieved from the nested path
    And the full object content should be preserved
    And the task should complete successfully

  Scenario: Get S3 object from different regions
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 111122223333              |
      | key                   | templates/infrastructure.yaml |
      | region                | eu-central-1              |
    And the S3 bucket "sc-puppet-parameters-111122223333" exists in eu-central-1
    And the template object exists in the bucket
    When I run the task
    Then the S3 object should be retrieved from the specified region
    And the template content should be accessible
    And cross-region access should work correctly

  Scenario: Get large S3 object
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 444455556666              |
      | key                   | data/large-dataset.json   |
      | region                | ap-southeast-2            |
    And the S3 bucket "sc-puppet-parameters-444455556666" exists
    And a large object exists in the bucket
    When I run the task
    Then the large S3 object should be retrieved completely
    And the entire content should be written to output
    And memory usage should be managed appropriately

  Scenario: Handle S3 object not found
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 777788889999              |
      | key                   | missing/file.txt          |
      | region                | ca-central-1              |
    And the S3 bucket "sc-puppet-parameters-777788889999" exists
    And the object "missing/file.txt" does not exist in the bucket
    When I run the task
    Then a NoSuchKey error should be raised
    And appropriate error information should be logged
    And the task should fail with a clear error message

  Scenario: Handle S3 bucket access denied
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 888899990000              |
      | key                   | restricted/secret.json    |
      | region                | us-east-1                 |
    And the S3 bucket "sc-puppet-parameters-888899990000" exists
    And access to the object is denied due to insufficient permissions
    When I run the task
    Then an AccessDenied error should be raised
    And the error should indicate permission issues
    And the task should fail gracefully

  Scenario: Get S3 object with binary content
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 123456789012              |
      | key                   | assets/image.png          |
      | region                | us-west-1                 |
    And the S3 bucket "sc-puppet-parameters-123456789012" exists
    And a binary object (image file) exists in the bucket
    When I run the task
    Then the binary S3 object should be retrieved correctly
    And the binary content should be preserved without corruption
    And no JSON encoding should be applied to the binary data

  Scenario: Get S3 object using standard puppet parameters bucket naming
    Given a GetS3ObjectTask with the following attributes:
      | attribute              | value                     |
      | account_id            | 555566667777              |
      | key                   | puppet/manifest-params.json |
      | region                | ap-northeast-1            |
    When I run the task
    Then the task should use the standard bucket naming convention "sc-puppet-parameters-{account_id}"
    And the object should be retrieved from "sc-puppet-parameters-555566667777"
    And the puppet parameter file should be accessed successfully
    And the content should be available for subsequent workflow tasks