#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class ShareAndAcceptPortfolioForAccountTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    share_tag_options = luigi.BoolParameter()
    portfolio_task_reference = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "share_tag_options": self.share_tag_options,
        }

    def has_already_been_shared(self, portfolio_id):
        with self.hub_regional_client("servicecatalog") as servicecatalog:
            p = dict(PortfolioId=portfolio_id)
            has_more = True
            while has_more:
                response = servicecatalog.list_portfolio_access(**p)
                if self.account_id in response.get("AccountIds"):
                    return True
                if response.get("NextPageToken"):
                    p["PageToken"] = response.get("NextPageToken")
                else:
                    has_more = False
        return False

    def accept_if_needed(self, portfolio_id):
        accepted = False
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            paginator = servicecatalog.get_paginator("list_accepted_portfolio_shares")
            for page in paginator.paginate(PortfolioShareType="IMPORTED"):
                for portfolio_detail in page.get("PortfolioDetails", []):
                    if portfolio_detail.get("Id") == portfolio_id:
                        accepted = True
        if not accepted:
            servicecatalog.accept_portfolio_share(PortfolioId=portfolio_id)
            return True
        return False

    def run(self):
        hub_portfolio_details = self.get_output_from_reference_dependency(
            self.portfolio_task_reference
        )
        portfolio_id = hub_portfolio_details.get("Id")

        # SHARE
        has_already_been_shared = self.has_already_been_shared(portfolio_id)
        if not has_already_been_shared:
            self.info(f"sharing {portfolio_id} with {self.account_id}")
            with self.hub_regional_client("servicecatalog") as servicecatalog:
                servicecatalog.create_portfolio_share(
                    PortfolioId=portfolio_id,
                    AccountId=self.account_id,
                    ShareTagOptions=self.share_tag_options,
                )

        # ACCEPT
        accepted = self.accept_if_needed(portfolio_id)

        self.write_empty_output()
