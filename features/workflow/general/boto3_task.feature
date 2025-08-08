Feature: Boto3 Task
  As a Service Catalog Puppet user
  I want to execute AWS API calls and extract specific data using JMESPath filters
  So that I can retrieve and process AWS resource information for my workflows

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have proper client configurations

  Scenario: Execute simple boto3 API call without pagination
    Given a Boto3Task with the following attributes:
      | attribute      | value                                   |
      | account_id     | 123456789012                           |
      | region         | us-east-1                              |
      | client         | ec2                                    |
      | use_paginator  | false                                  |
      | call           | describe_vpcs                          |
      | arguments      | {}                                     |
      | filter         | Vpcs[0].VpcId                          |
    When I run the task
    Then the AWS API call should be executed without pagination
    And the result should be filtered using the JMESPath expression
    And the filtered result should be written to output
    And the task should complete successfully

  Scenario: Execute boto3 API call with pagination
    Given a Boto3Task with the following attributes:
      | attribute      | value                                   |
      | account_id     | 987654321098                           |
      | region         | eu-west-1                              |
      | client         | s3                                     |
      | use_paginator  | true                                   |
      | call           | list_objects_v2                        |
      | arguments      | {"Bucket": "my-test-bucket"}           |
      | filter         | Contents[*].Key                        |
    When I run the task
    Then the AWS API call should be executed with pagination
    And all pages should be merged into a single result
    And the result should be filtered using the JMESPath expression
    And the filtered result should be written to output

  Scenario: Execute API call with complex arguments and filter
    Given a Boto3Task with the following attributes:
      | attribute      | value                                                    |
      | account_id     | 111122223333                                            |
      | region         | ap-southeast-1                                          |
      | client         | ec2                                                     |
      | use_paginator  | false                                                   |
      | call           | describe_instances                                      |
      | arguments      | {"Filters": [{"Name": "instance-state-name", "Values": ["running"]}]} |
      | filter         | Reservations[*].Instances[*].InstanceId                 |
    When I run the task
    Then the AWS API call should include the complex filter arguments
    And the JMESPath filter should extract instance IDs from nested structures
    And the result should be a list of running instance IDs
    And the filtered result should be written to output

  Scenario: Handle string result with whitespace trimming
    Given a Boto3Task with the following attributes:
      | attribute      | value                                   |
      | account_id     | 444455556666                           |
      | region         | us-west-2                              |
      | client         | ec2                                    |
      | use_paginator  | false                                  |
      | call           | describe_vpcs                          |
      | arguments      | {"VpcIds": ["vpc-12345678"]}           |
      | filter         | Vpcs[0].Tags[?Key=='Name'].Value[0]    |
    When I run the task
    And the API returns a string value with leading/trailing whitespace
    Then the whitespace should be automatically trimmed
    And the cleaned string result should be written to output

  Scenario: Execute CloudFormation API call with pagination
    Given a Boto3Task with the following attributes:
      | attribute      | value                                   |
      | account_id     | 777788889999                           |
      | region         | ca-central-1                           |
      | client         | cloudformation                         |
      | use_paginator  | true                                   |
      | call           | list_stacks                            |
      | arguments      | {"StackStatusFilter": ["CREATE_COMPLETE"]} |
      | filter         | StackSummaries[*].StackName            |
    When I run the task
    Then all pages of CloudFormation stacks should be retrieved
    And only stacks with CREATE_COMPLETE status should be included
    And the result should be a list of stack names
    And the filtered result should be written to output

  Scenario: Execute IAM API call for role information
    Given a Boto3Task with the following attributes:
      | attribute      | value                                   |
      | account_id     | 888899990000                           |
      | region         | us-east-1                              |
      | client         | iam                                    |
      | use_paginator  | false                                  |
      | call           | get_role                               |
      | arguments      | {"RoleName": "MyServiceRole"}          |
      | filter         | Role.Arn                               |
    When I run the task
    Then the IAM role information should be retrieved
    And the role ARN should be extracted using JMESPath
    And the ARN should be written to output

  Scenario: Handle complex nested filter with multiple conditions
    Given a Boto3Task with the following attributes:
      | attribute      | value                                                           |
      | account_id     | 999000111222                                                   |
      | region         | eu-central-1                                                   |
      | client         | ec2                                                            |
      | use_paginator  | false                                                          |
      | call           | describe_security_groups                                       |
      | arguments      | {"Filters": [{"Name": "group-name", "Values": ["my-sg"]}]}     |
      | filter         | SecurityGroups[0].IpPermissions[?FromPort==`80`].IpRanges[0].CidrIp |
    When I run the task
    Then the security group details should be retrieved
    And the filter should extract CIDR blocks for port 80 rules
    And the specific CIDR block should be written to output

  Scenario: Handle API call failure gracefully
    Given a Boto3Task with the following attributes:
      | attribute      | value                                   |
      | account_id     | 123456789012                           |
      | region         | us-east-1                              |
      | client         | ec2                                    |
      | use_paginator  | false                                  |
      | call           | describe_instances                     |
      | arguments      | {"InstanceIds": ["i-nonexistent"]}     |
      | filter         | Reservations[0].Instances[0].InstanceId |
    When I run the task
    And the instance does not exist
    Then the task should handle the API error appropriately
    And relevant error information should be logged