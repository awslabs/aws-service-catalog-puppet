#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class ShareAndAcceptPortfolioForAccountTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    share_tag_options = luigi.BoolParameter()
    share_principals = luigi.BoolParameter()
    portfolio_task_reference = luigi.Parameter()
    describe_portfolio_shares_task_ref = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "share_tag_options": self.share_tag_options,
            "share_principals": self.share_principals,
            "cache_invalidator": self.cache_invalidator,
        }

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
        portfolio_id = self.get_attribute_from_output_from_reference_dependency(
            "Id", self.portfolio_task_reference
        )

        changes = dict()
        existing_share_details = self.get_attribute_from_output_from_reference_dependency(
            self.account_id, self.describe_portfolio_shares_task_ref
        )

        if existing_share_details:
            if existing_share_details.get("ShareTagOptions") != self.share_tag_options:
                changes["ShareTagOptions"] = self.share_tag_options

            if changes:
                with self.hub_regional_client("servicecatalog") as servicecatalog:
                    servicecatalog.update_portfolio_share(
                        PortfolioId=portfolio_id, AccountId=self.account_id, **changes
                    )
        else:
            # SHARE
            self.info(f"sharing {portfolio_id} with {self.account_id}")
            with self.hub_regional_client("servicecatalog") as servicecatalog:
                servicecatalog.create_portfolio_share(
                    PortfolioId=portfolio_id,
                    AccountId=self.account_id,
                    ShareTagOptions=self.share_tag_options,
                )

            # ACCEPT
            self.accept_if_needed(portfolio_id)

        self.write_empty_output()
