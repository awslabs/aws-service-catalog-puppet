Feature: Get Or Create Organizational Unit Task
  As a Service Catalog Puppet user
  I want to get or create organizational units in AWS Organizations
  So that I can manage account organization structure

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And AWS Organizations service is available

  Scenario: Create new organizational unit successfully
    Given a GetOrCreateOrganizationalUnitTask with the following attributes:
      | attribute         | value                          |
      | region           | us-east-1                      |
      | account_id       | 123456789012                   |
      | path             | /Security/Development          |
      | parent_ou_id     | ou-parent123456                |
      | name             | Development                    |
      | parent_ou_task_ref | parent-ou-ref-123            |
    And tags:
      | tag_key       | tag_value     |
      | Environment   | Development   |
      | Purpose       | Testing       |
    And no organizational unit exists with the specified name in the parent
    When I run the task
    Then a new organizational unit should be created
    And the organizational unit should be tagged with the specified tags
    And the task should return the organizational unit ID
    And the task should complete successfully

  Scenario: Get existing organizational unit
    Given a GetOrCreateOrganizationalUnitTask with the following attributes:
      | attribute         | value                          |
      | region           | us-west-2                      |
      | account_id       | 987654321098                   |
      | path             | /Production/Web                |
      | parent_ou_id     | ou-parent789012                |
      | name             | Web                            |
      | parent_ou_task_ref | parent-ou-ref-456            |
    And tags:
      | tag_key       | tag_value     |
      | Environment   | Production    |
      | Team          | WebDev        |
    And an organizational unit already exists with the specified name in the parent
    When I run the task
    Then the existing organizational unit should be returned
    And no new organizational unit should be created
    And the task should return the existing organizational unit ID
    And the task should complete successfully

  Scenario: Handle organizational unit creation with nested path
    Given a GetOrCreateOrganizationalUnitTask with the following attributes:
      | attribute         | value                          |
      | region           | eu-central-1                   |
      | account_id       | 111122223333                   |
      | path             | /Company/IT/Security/Compliance|
      | parent_ou_id     | ou-parent345678                |
      | name             | Compliance                     |
      | parent_ou_task_ref | parent-ou-ref-789            |
    And tags:
      | tag_key       | tag_value     |
      | Department    | Security      |
      | Level         | L4            |
    When I run the task
    Then the organizational unit should be created in the correct hierarchical position
    And the full path should be maintained
    And the task should complete successfully

  Scenario: Create organizational unit with dependency on parent OU task
    Given a GetOrCreateOrganizationalUnitTask with the following attributes:
      | attribute         | value                          |
      | region           | ap-southeast-1                 |
      | account_id       | 444455556666                   |
      | path             | /Marketing/Digital             |
      | parent_ou_id     | ou-parent901234                |
      | name             | Digital                        |
      | parent_ou_task_ref | marketing-parent-task-ref    |
    And the parent organizational unit task must complete first
    When I run the task
    Then the task should wait for the parent OU task to complete
    And then create the organizational unit
    And the task should complete successfully

  Scenario: Handle organizational unit creation failure
    Given a GetOrCreateOrganizationalUnitTask with the following attributes:
      | attribute         | value                          |
      | region           | ca-central-1                   |
      | account_id       | 777788889999                   |
      | path             | /Finance/Accounting            |
      | parent_ou_id     | ou-invalid-parent              |
      | name             | Accounting                     |
      | parent_ou_task_ref | parent-ou-ref-invalid        |
    And the parent organizational unit does not exist
    When I run the task
    Then an appropriate error should be raised
    And the error should indicate the parent OU is invalid
    And the task should fail gracefully