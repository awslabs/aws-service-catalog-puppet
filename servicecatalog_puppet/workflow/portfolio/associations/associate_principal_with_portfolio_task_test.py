#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class AssociatePrincipalWithPortfolioTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    account_id = "account_id"
    region = "region"
    portfolio = "portfolio"
    portfolio_id = "portfolio_id"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.portfolio.associations import (
            associate_principal_with_portfolio_task,
        )

        self.module = associate_principal_with_portfolio_task

        self.sut = self.module.AssociatePrincipalWithPortfolioTask(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            portfolio_id=self.portfolio_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "region": self.region,
            "account_id": self.account_id,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = {
            f"servicecatalog.associate_principal_with_portfolio_{self.region}": 1,
            f"servicecatalog.list_principals_for_portfolio_single_page_{self.region}": 1,
        }

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
