Feature: Import Into Spoke Local Portfolio Task
  As a Service Catalog Puppet user
  I want to import products from hub portfolio into spoke local portfolios
  So that I can make products available in specific accounts with local portfolio management

  Background:
    Given I have the necessary AWS permissions
    And the target account and region are accessible
    And Service Catalog service is available
    And both hub and spoke portfolios exist

  Scenario: Import products into spoke local portfolio successfully
    Given an ImportIntoSpokeLocalPortfolioTask with the following attributes:
      | attribute                                                 | value                          |
      | account_id                                               | 123456789012                   |
      | region                                                   | us-east-1                      |
      | portfolio_task_reference                                 | spoke-portfolio-ref-123        |
      | hub_portfolio_task_reference                             | hub-portfolio-ref-456          |
      | portfolio_get_all_products_and_their_versions_ref        | spoke-products-ref-789         |
      | portfolio_get_all_products_and_their_versions_for_hub_ref| hub-products-ref-012           |
    And the spoke portfolio exists with ID "port-spoke123"
    And the hub portfolio exists with ID "port-hub456"
    And the hub portfolio contains products not present in spoke portfolio
    When I run the task
    Then products should be imported from hub portfolio to spoke portfolio
    And product versions should be synchronized
    And the task should complete successfully

  Scenario: Skip import when products are already synchronized
    Given an ImportIntoSpokeLocalPortfolioTask with the following attributes:
      | attribute                                                 | value                          |
      | account_id                                               | 987654321098                   |
      | region                                                   | us-west-2                      |
      | portfolio_task_reference                                 | spoke-portfolio-ref-234        |
      | hub_portfolio_task_reference                             | hub-portfolio-ref-567          |
      | portfolio_get_all_products_and_their_versions_ref        | spoke-products-ref-890         |
      | portfolio_get_all_products_and_their_versions_for_hub_ref| hub-products-ref-123           |
    And the spoke portfolio exists with ID "port-spoke234"
    And the hub portfolio exists with ID "port-hub567" 
    And the spoke portfolio already contains all products from the hub portfolio
    When I run the task
    Then no products should be imported
    And the task should complete without making changes
    And appropriate logging should indicate products are already synchronized

  Scenario: Import specific product versions from hub to spoke
    Given an ImportIntoSpokeLocalPortfolioTask with the following attributes:
      | attribute                                                 | value                          |
      | account_id                                               | 111122223333                   |
      | region                                                   | eu-central-1                   |
      | portfolio_task_reference                                 | spoke-portfolio-ref-345        |
      | hub_portfolio_task_reference                             | hub-portfolio-ref-678          |
      | portfolio_get_all_products_and_their_versions_ref        | spoke-products-ref-901         |
      | portfolio_get_all_products_and_their_versions_for_hub_ref| hub-products-ref-234           |
    And the spoke portfolio exists with ID "port-spoke345"
    And the hub portfolio contains products with multiple versions
    And the spoke portfolio has outdated versions of some products
    When I run the task
    Then the latest product versions should be imported from hub
    And existing products should be updated to latest versions
    And new products should be added to the spoke portfolio
    And version synchronization should be completed

  Scenario: Handle import when spoke portfolio is empty
    Given an ImportIntoSpokeLocalPortfolioTask with the following attributes:
      | attribute                                                 | value                          |
      | account_id                                               | 444455556666                   |
      | region                                                   | ap-southeast-2                 |
      | portfolio_task_reference                                 | spoke-portfolio-ref-456        |
      | hub_portfolio_task_reference                             | hub-portfolio-ref-789          |
      | portfolio_get_all_products_and_their_versions_ref        | spoke-products-ref-012         |
      | portfolio_get_all_products_and_their_versions_for_hub_ref| hub-products-ref-345           |
    And the spoke portfolio exists with ID "port-spoke456"
    And the spoke portfolio is empty (contains no products)
    And the hub portfolio contains multiple products
    When I run the task
    Then all products from hub portfolio should be imported
    And all product versions should be copied to spoke portfolio
    And the spoke portfolio should match the hub portfolio content
    And the task should complete successfully

  Scenario: Import with cross-region portfolio synchronization
    Given an ImportIntoSpokeLocalPortfolioTask with the following attributes:
      | attribute                                                 | value                          |
      | account_id                                               | 777788889999                   |
      | region                                                   | ca-central-1                   |
      | portfolio_task_reference                                 | spoke-portfolio-ref-567        |
      | hub_portfolio_task_reference                             | hub-portfolio-ref-890          |
      | portfolio_get_all_products_and_their_versions_ref        | spoke-products-ref-123         |
      | portfolio_get_all_products_and_their_versions_for_hub_ref| hub-products-ref-456           |
    And the hub portfolio is in a different region
    And both portfolios exist and are accessible
    When I run the task
    Then cross-region product import should succeed
    And product metadata should be preserved during import
    And regional constraints should be handled appropriately
    And the task should complete successfully

  Scenario: Handle import failure when hub portfolio is not accessible
    Given an ImportIntoSpokeLocalPortfolioTask with the following attributes:
      | attribute                                                 | value                          |
      | account_id                                               | 888899990000                   |
      | region                                                   | us-east-1                      |
      | portfolio_task_reference                                 | spoke-portfolio-ref-678        |
      | hub_portfolio_task_reference                             | invalid-hub-portfolio-ref      |
      | portfolio_get_all_products_and_their_versions_ref        | spoke-products-ref-234         |
      | portfolio_get_all_products_and_their_versions_for_hub_ref| invalid-hub-products-ref       |
    And the spoke portfolio exists
    And the hub portfolio reference is invalid or inaccessible
    When I run the task
    Then an appropriate error should be raised
    And the error should indicate hub portfolio access failure
    And the spoke portfolio should remain unchanged
    And the task should fail gracefully