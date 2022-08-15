#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow.dependencies import tasks


class ShareAndAcceptPortfolioForAccountTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    portfolio_task_reference = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_accepted_portfolio_shares_{self.account_id}_{self.region}",
            f"servicecatalog.list_portfolio_access_{self.account_id}_{self.region}",
            f"servicecatalog.create_portfolio_share_{self.account_id}_{self.region}",
            f"servicecatalog.accept_portfolio_share_{self.account_id}_{self.region}",
            # f"servicecatalog.list_principals_for_portfolio_{self.account_id}_{self.region}",
            # f"servicecatalog.associate_principal_with_portfolio_{self.account_id}_{self.region}",
        ]

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

    # def add_principal_if_needed(self, portfolio_id, account_to_add, servicecatalog):
    #     was_present = False
    #     principal_to_associate = config.get_puppet_role_arn(account_to_add)
    #     paginator = servicecatalog.get_paginator("list_principals_for_portfolio")
    #     for page in paginator.paginate(PortfolioId=portfolio_id):
    #         self.info(page)
    #         for principal in page.get("Principals", []):
    #             if principal_to_associate == principal.get("PrincipalARN"):
    #                 was_present = True
    #
    #     if not was_present:
    #         servicecatalog.associate_principal_with_portfolio(
    #             PortfolioId=portfolio_id,
    #             PrincipalARN=principal_to_associate,
    #             PrincipalType="IAM",
    #         )
    #         return True
    #     return False

    def run(self):
        hub_portfolio_details = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_task_reference)
            .open("r")
            .read()
        )
        portfolio_id = hub_portfolio_details.get("Id")
        # # ADD PRINCIPAL IF NEEDED
        # with self.hub_regional_client("servicecatalog") as servicecatalog:
        #     hub_added_principal = self.add_principal_if_needed(
        #         portfolio_id, self.puppet_account_id, servicecatalog
        #     )

        # SHARE
        has_already_been_shared = self.has_already_been_shared(portfolio_id)
        if not has_already_been_shared:
            self.info(f"{self.uid}: sharing {portfolio_id} with {self.account_id}")
            with self.hub_regional_client("servicecatalog") as servicecatalog:
                servicecatalog.create_portfolio_share(
                    PortfolioId=portfolio_id, AccountId=self.account_id,
                )

        # ACCEPT
        accepted = self.accept_if_needed(portfolio_id)

        self.write_output(
            dict(
                has_already_been_shared=has_already_been_shared,
                accepted=accepted,
                hub_added_principal=False,
            )
        )
