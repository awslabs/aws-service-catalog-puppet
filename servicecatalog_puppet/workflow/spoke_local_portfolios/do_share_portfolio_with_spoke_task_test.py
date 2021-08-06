#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoSharePortfolioWithSpokeTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    spoke_local_portfolio_name = "spoke_local_portfolio_name"
    puppet_account_id = "puppet_account_id"
    sharing_mode = "sharing_mode"
    product_generation_method = "product_generation_method"
    organization = "organization"
    associations = []
    launch_constraints = {}
    portfolio = "portfolio"
    region = "region"
    account_id = "account_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.spoke_local_portfolios import (
            do_share_portfolio_with_spoke_task,
        )

        self.module = do_share_portfolio_with_spoke_task

        self.sut = self.module.DoSharePortfolioWithSpokeTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            puppet_account_id=self.puppet_account_id,
            sharing_mode=self.sharing_mode,
            product_generation_method=self.product_generation_method,
            organization=self.organization,
            associations=self.associations,
            launch_constraints=self.launch_constraints,
            portfolio=self.portfolio,
            region=self.region,
            account_id=self.account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
