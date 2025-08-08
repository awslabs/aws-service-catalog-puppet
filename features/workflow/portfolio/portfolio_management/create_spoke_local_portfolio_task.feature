Feature: Create Spoke Local Portfolio Task
  As a Service Catalog Puppet user
  I want to create Service Catalog portfolios in spoke accounts
  So that I can make products available for deployment in target accounts

  Background:
    Given I have the necessary AWS permissions
    And the target spoke account and region are accessible
    And I have Service Catalog portfolio management permissions
    And the hub portfolio information is available

  Scenario: Create spoke local portfolio in same account as hub
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 123456789012                 |
      | region                     | us-east-1                    |
      | portfolio                  | MyInfrastructurePortfolio    |
      | portfolio_task_reference   | hub-portfolio-ref-123        |
    And the puppet account ID is the same as the target account ID
    When I run the task
    Then the existing portfolio should be found in the account
    And no new portfolio should be created
    And the portfolio details should be written to output

  Scenario: Create new spoke local portfolio in different account
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 987654321098                 |
      | region                     | eu-west-1                    |
      | portfolio                  | SharedServicesPortfolio      |
      | portfolio_task_reference   | hub-portfolio-ref-456        |
    And the puppet account ID is different from the target account ID
    And the hub portfolio has the following details:
      | property     | value                                    |
      | ProviderName | Infrastructure Team                      |
      | Description  | Shared infrastructure services portfolio |
    When I run the task
    Then a new portfolio should be created in the spoke account
    And the portfolio should use the hub portfolio's ProviderName
    And the portfolio should use the hub portfolio's Description
    And the portfolio should be named "SharedServicesPortfolio"
    And the portfolio details should be written to output

  Scenario: Ensure existing spoke portfolio is maintained
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 111122223333                 |
      | region                     | ap-southeast-1               |
      | portfolio                  | CompliancePortfolio          |
      | portfolio_task_reference   | hub-portfolio-ref-789        |
    And the puppet account ID is different from the target account ID
    And a portfolio with the same name already exists in the spoke account
    When I run the task
    Then the existing portfolio should be updated if necessary
    And the portfolio details should match the hub portfolio configuration
    And the portfolio ID should remain the same if no changes are needed
    And the portfolio details should be written to output

  Scenario: Handle cross-region portfolio creation
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 444455556666                 |
      | region                     | us-west-2                    |
      | portfolio                  | RegionalServicesPortfolio    |
      | portfolio_task_reference   | hub-portfolio-ref-012        |
    And the puppet account ID is different from the target account ID
    When I run the task
    Then the portfolio should be created in the specified region
    And the regional Service Catalog client should be used
    And the portfolio should be available in us-west-2

  Scenario: Create portfolio with detailed hub portfolio information
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 777788889999                 |
      | region                     | ca-central-1                 |
      | portfolio                  | DataPlatformPortfolio        |
      | portfolio_task_reference   | hub-portfolio-ref-345        |
    And the puppet account ID is different from the target account ID
    And the hub portfolio has comprehensive details:
      | property     | value                                              |
      | ProviderName | Data Engineering Team                              |
      | Description  | Comprehensive data platform and analytics services |
      | Tags         | [{"Key": "Environment", "Value": "Production"}]    |
    When I run the task
    Then the spoke portfolio should inherit all relevant properties from hub
    And the provider name should be set to "Data Engineering Team"
    And the description should match the hub portfolio
    And the portfolio should be properly configured for the spoke account

  Scenario: Handle portfolio creation with dependency resolution
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 888899990000                 |
      | region                     | eu-central-1                 |
      | portfolio                  | SecurityPortfolio            |
      | portfolio_task_reference   | hub-portfolio-ref-678        |
    And the task depends on a hub portfolio task reference
    When I run the task
    Then the hub portfolio details should be retrieved from the dependency
    And the dependency output should be used for portfolio creation
    And the spoke portfolio should be created with the dependency data
    And proper task ordering should be maintained

  Scenario: Handle Service Catalog API errors gracefully
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 999000111222                 |
      | region                     | ap-northeast-1               |
      | portfolio                  | FailingPortfolio             |
      | portfolio_task_reference   | hub-portfolio-ref-901        |
    When I run the task
    And the Service Catalog API returns an error
    Then the task should handle the error appropriately
    And relevant error information should be logged
    And the task should fail with meaningful error messages

  Scenario: Verify portfolio output structure
    Given a CreateSpokeLocalPortfolioTask with the following attributes:
      | attribute                  | value                        |
      | account_id                 | 123123123123                 |
      | region                     | us-east-2                    |
      | portfolio                  | OutputValidationPortfolio    |
      | portfolio_task_reference   | hub-portfolio-ref-234        |
    When I run the task
    Then the output should contain the portfolio details
    And the output should include the portfolio ID
    And the output should include the portfolio ARN
    And the output should be properly formatted for downstream tasks