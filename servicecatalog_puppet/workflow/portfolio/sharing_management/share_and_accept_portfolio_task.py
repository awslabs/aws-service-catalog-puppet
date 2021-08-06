#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)
from servicecatalog_puppet.workflow.portfolio.sharing_management import (
    share_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.sharing_management import (
    share_portfolio_via_orgs_task,
)


class ShareAndAcceptPortfolioTask(
    portfolio_management_task.PortfolioManagementTask, manifest_mixin.ManifestMixen
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    sharing_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "sharing_mode": self.sharing_mode,
        }

    def requires(self):
        requirements = dict(
            portfolio=get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.puppet_account_id,
                region=self.region,
            )
        )
        if self.sharing_mode == constants.SHARING_MODE_AWS_ORGANIZATIONS:
            ou_to_share_with = self.manifest.get_account(self.account_id).get(
                "expanded_from"
            )
            if ou_to_share_with is None:
                self.warning(
                    f"Sharing {self.portfolio} with {self.account_id} not using orgs as there is no OU set for it"
                )
                requirements["share"] = share_portfolio_task.SharePortfolioTask(
                    manifest_file_path=self.manifest_file_path,
                    portfolio=self.portfolio,
                    account_id=self.account_id,
                    region=self.region,
                    puppet_account_id=self.puppet_account_id,
                )
            else:
                requirements[
                    "share"
                ] = share_portfolio_via_orgs_task.SharePortfolioViaOrgsTask(
                    manifest_file_path=self.manifest_file_path,
                    portfolio=self.portfolio,
                    region=self.region,
                    puppet_account_id=self.puppet_account_id,
                    ou_to_share_with=ou_to_share_with,
                )

        else:
            requirements["share"] = share_portfolio_task.SharePortfolioTask(
                manifest_file_path=self.manifest_file_path,
                portfolio=self.portfolio,
                account_id=self.account_id,
                region=self.region,
                puppet_account_id=self.puppet_account_id,
            )
        return requirements

    def api_calls_used(self):
        return [
            f"servicecatalog.list_accepted_portfolio_shares_single_page{self.account_id}_{self.region}",
            f"servicecatalog.accept_portfolio_share{self.account_id}_{self.region}",
            f"servicecatalog.associate_principal_with_portfolio{self.account_id}_{self.region}",
            f"servicecatalog.list_principals_for_portfolio{self.account_id}_{self.region}",
        ]

    def run(self):
        portfolio = self.load_from_input("portfolio")
        portfolio_id = portfolio.get("portfolio_id")

        with self.spoke_regional_client(
            "servicecatalog"
        ) as cross_account_servicecatalog:
            if self.sharing_mode != constants.SHARING_MODE_AWS_ORGANIZATIONS:
                was_accepted = False
                accepted_portfolio_shares = cross_account_servicecatalog.list_accepted_portfolio_shares_single_page().get(
                    "PortfolioDetails"
                )
                for accepted_portfolio_share in accepted_portfolio_shares:
                    if accepted_portfolio_share.get("Id") == portfolio_id:
                        was_accepted = True
                        break
                if not was_accepted:
                    self.info(f"{self.uid}: accepting {portfolio_id}")
                    cross_account_servicecatalog.accept_portfolio_share(
                        PortfolioId=portfolio_id
                    )

            principals_for_portfolio = cross_account_servicecatalog.list_principals_for_portfolio_single_page(
                PortfolioId=portfolio_id
            ).get(
                "Principals"
            )
            puppet_role_needs_associating = True
            principal_to_associate = config.get_puppet_role_arn(self.account_id)
            self.info(f"Checking if {principal_to_associate} needs to be associated")
            for principal_for_portfolio in principals_for_portfolio:
                self.info(
                    f"comparing {principal_to_associate} to {principal_for_portfolio.get('PrincipalARN')}"
                )
                if (
                    principal_for_portfolio.get("PrincipalARN")
                    == principal_to_associate
                ):
                    self.info("found a match!! no longer going to add")
                    puppet_role_needs_associating = False

            if puppet_role_needs_associating:
                cross_account_servicecatalog.associate_principal_with_portfolio(
                    PortfolioId=portfolio_id,
                    PrincipalARN=principal_to_associate,
                    PrincipalType="IAM",
                )

        self.write_output(self.param_kwargs)
