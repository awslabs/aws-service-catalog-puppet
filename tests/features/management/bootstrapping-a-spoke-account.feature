@behavioural @management @spoke-account
Feature: bootstrapping a spoke account
  As an operator
  I would like to be able to bootstrap a spoke account
  So I can provision resources into it

  Scenario: First bootstrap
    Given a "spoke" account has not been bootstrapped
    When I bootstrap a "spoke" account with version "x"
    Then the "spoke" account is bootstrapped with version "x"

  Scenario: Repeat bootstrap
    Given a "spoke" account has been bootstrapped with version "x"
    When I bootstrap a "spoke" account with version "x"
    Then the "spoke" account is bootstrapped with version "x"

  @wip
  Scenario: Bootstrap new version
    Given a "spoke" account has been bootstrapped with version "x"
    When I bootstrap a "spoke" account with version "y"
    Then the "spoke" account is bootstrapped with version "y"
