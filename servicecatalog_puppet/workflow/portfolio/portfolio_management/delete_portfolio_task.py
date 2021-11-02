#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import utils
from servicecatalog_puppet.workflow.general import delete_cloud_formation_stack_task
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    delete_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    disassociate_products_from_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)
from servicecatalog_puppet.workflow.portfolio.sharing_management import (
    delete_portfolio_share_task,
)


class DeletePortfolio(portfolio_management_task.PortfolioManagementTask):
    spoke_local_portfolio_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    product_generation_method = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_portfolios_single_page_{self.account_id}_{self.region}",
        ]

    def requires(self):
        return [
            delete_cloud_formation_stack_task.DeleteCloudFormationStackTask(
                account_id=self.account_id,
                region=self.region,
                stack_name=f"associations-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}",
                nonce=self.cache_invalidator,
            ),
        ]

    def run(self):
        is_puppet_account = self.account_id == self.puppet_account_id
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            result = None
            self.info("Checking portfolios for a match")
            response = servicecatalog.list_portfolios_single_page()
            for portfolio_detail in response.get("PortfolioDetails", []):
                if portfolio_detail.get("DisplayName") == self.portfolio:
                    result = portfolio_detail
                    self.info(f"Found a non-imported portfolio: {result}")
                    break
            if result:
                portfolio_id = result.get("Id")

                if not is_puppet_account:
                    yield disassociate_products_from_portfolio_task.DisassociateProductsFromPortfolio(
                        account_id=self.account_id,
                        region=self.region,
                        portfolio_id=portfolio_id,
                        manifest_file_path=self.manifest_file_path,
                    )
                    yield delete_local_portfolio_task.DeleteLocalPortfolio(
                        account_id=self.account_id,
                        region=self.region,
                        portfolio_id=portfolio_id,
                        manifest_file_path=self.manifest_file_path,
                    )

            if not is_puppet_account:
                yield delete_portfolio_share_task.DeletePortfolioShare(
                    account_id=self.account_id,
                    region=self.region,
                    portfolio=self.portfolio,
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                )
        self.write_output(self.params_for_results_display())
