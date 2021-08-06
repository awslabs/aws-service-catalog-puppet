#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import os

import luigi

from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)


class RequestPolicyTask(portfolio_management_task.PortfolioManagementTask):
    type = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()
    organization = luigi.Parameter(default=None)

    def params_for_results_display(self):
        return {
            "type": self.type,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        if self.organization is not None:
            p = f"data/{self.type}/{self.region}/organizations/"
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
            path = f"{p}/{self.organization}.json"
        else:
            p = f"data/{self.type}/{self.region}/accounts/"
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
            path = f"{p}/{self.account_id}.json"

        f = open(path, "w")
        f.write(json.dumps(self.param_kwargs, indent=4, default=str,))
        f.close()
        self.write_output(self.param_kwargs)
