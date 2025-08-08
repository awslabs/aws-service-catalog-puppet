Feature: Do Assert Task
  As a Service Catalog Puppet user
  I want to validate expected values against actual AWS API responses
  So that I can ensure my infrastructure meets defined criteria and compliance requirements

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And I have assertion definitions with expected and actual configurations

  Scenario: Assert string value matches exactly
    Given a DoAssertTask with the following attributes:
      | attribute        | value                     |
      | assertion_name   | vpc-name-assertion        |
      | region           | us-east-1                 |
      | account_id       | 123456789012              |
      | execution        | spoke                     |
    And expected configuration:
      | config_key | config_value      |
      | value      | "my-production-vpc" |
    And actual configuration:
      | config_key    | config_value                    |
      | client        | ec2                             |
      | call          | describe_vpcs                   |
      | use_paginator | false                           |
      | filter        | Vpcs[0].Tags[?Key=='Name'].Value[0] |
      | arguments     | {"VpcIds": ["vpc-12345678"]}    |
    When I run the task
    And the AWS API returns the expected VPC name
    Then the assertion should pass
    And an empty output file should be written

  Scenario: Assert list values match ignoring order
    Given a DoAssertTask with the following attributes:
      | attribute        | value                     |
      | assertion_name   | security-group-rules      |
      | region           | eu-west-1                 |
      | account_id       | 987654321098              |
      | execution        | hub                       |
    And expected configuration:
      | config_key | config_value                           |
      | value      | ["80", "443", "22"]                    |
    And actual configuration:
      | config_key    | config_value                                  |
      | client        | ec2                                           |
      | call          | describe_security_groups                      |
      | use_paginator | false                                         |
      | filter        | SecurityGroups[0].IpPermissions[*].FromPort   |
      | arguments     | {"SecurityGroupIds": ["sg-abc123def"]}        |
    When I run the task
    And the AWS API returns ports in different order
    Then the assertion should pass because order is ignored
    And an empty output file should be written

  Scenario: Assert with paginated API call
    Given a DoAssertTask with the following attributes:
      | attribute        | value                     |
      | assertion_name   | s3-bucket-count           |
      | region           | us-west-2                 |
      | account_id       | 111122223333              |
      | execution        | spoke                     |
    And expected configuration:
      | config_key | config_value |
      | value      | 5            |
    And actual configuration:
      | config_key    | config_value                    |
      | client        | s3                              |
      | call          | list_buckets                    |
      | use_paginator | true                            |
      | filter        | length(Buckets)                 |
      | arguments     | {}                              |
    When I run the task
    And the paginated API returns multiple pages
    Then the assertion should aggregate all pages
    And verify the total bucket count
    And an empty output file should be written

  Scenario: Handle assertion failure with detailed diff
    Given a DoAssertTask with the following attributes:
      | attribute        | value                     |
      | assertion_name   | instance-state-check      |
      | region           | ap-southeast-1            |
      | account_id       | 444455556666              |
      | execution        | spoke                     |
    And expected configuration:
      | config_key | config_value |
      | value      | "running"    |
    And actual configuration:
      | config_key    | config_value                              |
      | client        | ec2                                       |
      | call          | describe_instances                        |
      | use_paginator | false                                     |
      | filter        | Reservations[0].Instances[0].State.Name   |
      | arguments     | {"InstanceIds": ["i-1234567890abcdef0"]}  |
    When I run the task
    And the actual instance state is "stopped"
    Then an exception should be raised with detailed diff information
    And the diff should show expected "running" vs actual "stopped"

  Scenario: Assert with complex nested object comparison
    Given a DoAssertTask with the following attributes:
      | attribute        | value                     |
      | assertion_name   | cloudformation-outputs    |
      | region           | ca-central-1              |
      | account_id       | 777788889999              |
      | execution        | hub                       |
    And expected configuration:
      | config_key | config_value                                    |
      | value      | {"VpcId": "vpc-abc123", "SubnetIds": ["subnet-def456"]} |
    And actual configuration:
      | config_key    | config_value                                    |
      | client        | cloudformation                                  |
      | call          | describe_stacks                                 |
      | use_paginator | false                                           |
      | filter        | Stacks[0].Outputs                               |
      | arguments     | {"StackName": "my-infrastructure-stack"}        |
    When I run the task
    And the CloudFormation stack outputs match the expected structure
    Then the assertion should pass
    And an empty output file should be written

  Scenario: Handle string whitespace normalization
    Given a DoAssertTask with the following attributes:
      | attribute        | value                     |
      | assertion_name   | tag-value-check           |
      | region           | eu-central-1              |
      | account_id       | 888899990000              |
      | execution        | spoke                     |
    And expected configuration:
      | config_key | config_value        |
      | value      | "Production Environment" |
    And actual configuration:
      | config_key    | config_value                                    |
      | client        | ec2                                             |
      | call          | describe_instances                              |
      | use_paginator | false                                           |
      | filter        | Reservations[0].Instances[0].Tags[?Key=='Environment'].Value[0] |
      | arguments     | {"InstanceIds": ["i-abcdef1234567890"]}         |
    When I run the task
    And the AWS API returns the value with leading/trailing whitespace
    Then the whitespace should be automatically trimmed
    And the assertion should pass
    And an empty output file should be written