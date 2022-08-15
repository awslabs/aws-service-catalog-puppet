#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow.dependencies import tasks

sharing_mode_map = dict(ACCOUNT="IMPORTED", AWS_ORGANIZATIONS="AWS_ORGANIZATIONS",)


class CreateAssociationTask(tasks.TaskWithReference):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
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
            f"servicecatalog.list_portfolios_{self.account_id}_{self.region}",
        ]

    def run(self):
        portfolio_details = self.get_output_from_reference_dependency(
            self.portfolio_task_reference
        )
        portfolio_id = portfolio_details.get("Id")

        was_present = False
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            principal_to_associate = config.get_puppet_role_arn(self.account_id)
            paginator = servicecatalog.get_paginator("list_principals_for_portfolio")
            for page in paginator.paginate(PortfolioId=portfolio_id):
                self.info(page)
                for principal in page.get("Principals", []):
                    if principal_to_associate == principal.get("PrincipalARN"):
                        was_present = True

            if not was_present:
                servicecatalog.associate_principal_with_portfolio(
                    PortfolioId=portfolio_id,
                    PrincipalARN=principal_to_associate,
                    PrincipalType="IAM",
                )

        self.write_output(dict(was_present=was_present))
