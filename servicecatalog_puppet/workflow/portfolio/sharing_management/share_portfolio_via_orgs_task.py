#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import time

import luigi
import yaml

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class SharePortfolioViaOrgsTask(portfolio_management_task.PortfolioManagementTask):
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    ou_to_share_with = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "ou_to_share_with": self.ou_to_share_with,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.create_portfolio_share",
            f"servicecatalog.describe_portfolio_share_status",
        ]

    def requires(self):
        return dict(
            portfolio=get_portfolio_by_portfolio_name_task.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                account_id=self.puppet_account_id,
                region=self.region,
            )
        )

    def run(self):
        portfolio_id = self.load_from_input("portfolio").get("portfolio_id")
        with self.hub_regional_client("servicecatalog") as servicecatalog:
            portfolio_share_token = servicecatalog.create_portfolio_share(
                PortfolioId=portfolio_id,
                OrganizationNode=dict(
                    Type="ORGANIZATIONAL_UNIT", Value=self.ou_to_share_with
                ),
            ).get("PortfolioShareToken")

            status = "NOT_STARTED"

            while status in ["NOT_STARTED", "IN_PROGRESS"]:
                time.sleep(5)
                response = servicecatalog.describe_portfolio_share_status(
                    PortfolioShareToken=portfolio_share_token
                )
                status = response.get("Status")
                self.info(f"New status: {status}")

            if status in ["COMPLETED_WITH_ERRORS", "ERROR"]:
                errors = list()
                for error in response.get("ShareDetails").get("ShareErrors"):
                    if error.get("Error") == "DuplicateResourceException":
                        self.warning(yaml.safe_dump(error))
                    else:
                        errors.append(error)
                if len(errors) > 0:
                    raise Exception(yaml.safe_dump(response.get("ShareDetails")))

        self.write_output(self.param_kwargs)
