#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import time

import luigi
import yaml

from servicecatalog_puppet.workflow.dependencies import tasks


class SharePortfolioViaOrgsTask(tasks.TaskWithReference):
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    share_tag_options = luigi.BoolParameter()
    ou_to_share_with = luigi.Parameter()
    portfolio_task_reference = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "ou_to_share_with": self.ou_to_share_with,
            "share_tag_options": self.share_tag_options,
        }

    def run(self):
        hub_portfolio_details = self.get_output_from_reference_dependency(
            self.portfolio_task_reference
        )
        portfolio_id = hub_portfolio_details.get("Id")

        with self.hub_regional_client("servicecatalog") as servicecatalog:
            portfolio_share_token = servicecatalog.create_portfolio_share(
                PortfolioId=portfolio_id,
                ShareTagOptions=self.share_tag_options,
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

        self.write_empty_output()
