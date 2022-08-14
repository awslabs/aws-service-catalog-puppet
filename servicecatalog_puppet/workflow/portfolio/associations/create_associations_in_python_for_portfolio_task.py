#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import time

import luigi

from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_portfolio_by_portfolio_name_task,
)
from servicecatalog_puppet.workflow.portfolio.associations import (
    associate_principal_with_portfolio_task,
)
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)

from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet import config


class CreateAssociationsInPythonForPortfolioTask(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    portfolio_task_reference = luigi.Parameter()
    task_reference = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

    portfolio = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
        }

    def requires(self):
        return dict(
            reference_dependencies=get_dependencies_for_task_reference(
                self.manifest_task_reference_file_path,
                self.task_reference,
                self.puppet_account_id,
            )
        )

    def run(self):
        portfolio_details = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_task_reference)
            .open("r")
            .read()
        )
        portfolio_id = portfolio_details.get("Id")

        principal_arn = config.get_puppet_role_arn(self.account_id)
        with self.hub_regional_client("servicecatalog") as servicecatalog:
            servicecatalog.associate_principal_with_portfolio(
                PortfolioId=portfolio_id,
                PrincipalARN=principal_arn,
                PrincipalType="IAM",
            )
            results = []
            needle = dict(PrincipalARN=principal_arn, PrincipalType="IAM")
            self.info(
                f"Checking for principal association of: {principal_arn} to: {portfolio_id}"
            )
            while needle not in results:
                self.info("- not found yet, still looking")
                time.sleep(1)
                results = servicecatalog.list_principals_for_portfolio_single_page(
                    PortfolioId=portfolio_id,
                ).get("Principals", [])

        self.write_output(self.param_kwargs)
