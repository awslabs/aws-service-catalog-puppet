@behavioural @management @puppet-account
Feature: bootstrapping a puppet account
  As an operator
  I would like to be able to bootstrap a puppet account
  So I can use the framework

  Scenario: First bootstrap
    Given a "puppet" account has not been bootstrapped
    And the config has been set
    When I bootstrap a "puppet" account with version "x"
    Then the "puppet" account is bootstrapped with version "x"

  Scenario: Repeat bootstrap
    Given a "puppet" account has been bootstrapped with version "x"
    When I bootstrap a "puppet" account with version "x"
    Then the "puppet" account is bootstrapped with version "x"

  @wip
  Scenario: Bootstrap new version
    Given a "puppet" account has been bootstrapped with version "x"
    When I bootstrap a "puppet" account with version "y"
    Then the "puppet" account is bootstrapped with version "y"
