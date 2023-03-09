#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class DescribePortfolioSharesTask(tasks.TaskWithReferenceAndCommonParameters):
    portfolio_task_reference = luigi.Parameter()
    type = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "region": self.region,
            "account_id": self.account_id,
            "portfolio_task_reference": self.portfolio_task_reference,
            "type": self.type,
        }

    def run(self):
        portfolio_id = self.get_attribute_from_output_from_reference_dependency(
            "Id", self.portfolio_task_reference
        )

        with self.spoke_regional_client("servicecatalog") as servicecatalog:
            has_more = True
            args = dict(PortfolioId=portfolio_id, Type=self.type,)
            shares = dict()
            while has_more:
                result = servicecatalog.describe_portfolio_shares(**args)
                for portfolio_share_detail in result.get("PortfolioShareDetails", []):
                    shares[
                        portfolio_share_detail.get("PrincipalId")
                    ] = portfolio_share_detail
                if result.get("NextPageToken"):
                    has_more = True
                    args["PageToken"] = result.get("NextPageToken")
                else:
                    has_more = False
            self.write_output(shares)
