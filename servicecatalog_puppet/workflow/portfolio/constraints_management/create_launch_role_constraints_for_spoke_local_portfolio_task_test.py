#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class CreateLaunchRoleConstraintsForSpokeLocalPortfolioTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    manifest_file_path = "manifest_file_path"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    puppet_account_id = "puppet_account_id"
    organization = "organization"
    product_generation_method = "product_generation_method"
    launch_constraints = {}
    sharing_mode = "sharing_mode"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.constraints_management import (
            create_launch_role_constraints_for_spoke_local_portfolio_task,
        )

        self.module = create_launch_role_constraints_for_spoke_local_portfolio_task

        self.sut = self.module.CreateLaunchRoleConstraintsForSpokeLocalPortfolioTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            puppet_account_id=self.puppet_account_id,
            organization=self.organization,
            product_generation_method=self.product_generation_method,
            launch_constraints=self.launch_constraints,
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
            f"cloudformation.ensure_deleted_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
            f"cloudformation.create_or_update_{self.account_id}_{self.region}",
            f"service_catalog.search_products_as_admin_{self.account_id}_{self.region}",
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
