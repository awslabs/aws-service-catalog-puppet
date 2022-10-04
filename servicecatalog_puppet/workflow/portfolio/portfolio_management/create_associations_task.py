#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import time

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow.dependencies import tasks


class CreateAssociationTask(tasks.TaskWithReference):
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

    def run(self):
        portfolio_details = self.get_output_from_reference_dependency(
            self.portfolio_task_reference
        )
        portfolio_id = portfolio_details.get("Id")

        principal_to_associate = config.get_puppet_role_arn(self.account_id)
        was_present = self.check_was_present(portfolio_id, principal_to_associate)
        self.info(f"Check for association: {was_present}")
        if not was_present:
            with self.spoke_regional_client("servicecatalog") as servicecatalog:
                servicecatalog.associate_principal_with_portfolio(
                    PortfolioId=portfolio_id,
                    PrincipalARN=principal_to_associate,
                    PrincipalType="IAM",
                )
        while not was_present:
            time.sleep(1)
            was_present = self.check_was_present(portfolio_id, principal_to_associate)
            self.info(f"Check for association: {was_present}")

        self.write_empty_output()

    def check_was_present(self, portfolio_id, principal_to_associate):
        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            paginator = servicecatalog.get_paginator("list_principals_for_portfolio")
            for page in paginator.paginate(PortfolioId=portfolio_id):
                for principal in page.get("Principals", []):
                    if principal_to_associate == principal.get("PrincipalARN"):
                        return True
        return False
