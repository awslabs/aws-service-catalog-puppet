#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class CreateAssociationsForSpokeLocalPortfolioTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    manifest_file_path = "manifest_file_path"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    puppet_account_id = "puppet_account_id"
    organization = "organization"
    associations = []
    sharing_mode = "sharing_mode"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.associations import (
            create_associations_for_spoke_local_portfolio_task,
        )

        self.module = create_associations_for_spoke_local_portfolio_task

        self.sut = self.module.CreateAssociationsForSpokeLocalPortfolioTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            puppet_account_id=self.puppet_account_id,
            organization=self.organization,
            associations=self.associations,
            sharing_mode=self.sharing_mode,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"cloudformation.create_or_update_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
        ]

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
