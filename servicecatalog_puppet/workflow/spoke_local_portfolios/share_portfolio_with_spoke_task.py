#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    do_share_portfolio_with_spoke_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_base_task,
)


class SharePortfolioWithSpokeTask(
    spoke_local_portfolio_base_task.SpokeLocalPortfolioBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    manifest_file_path = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    sharing_mode = luigi.Parameter()

    product_generation_method = luigi.Parameter()
    organization = luigi.Parameter()
    associations = luigi.ListParameter()
    launch_constraints = luigi.DictParameter()
    portfolio = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(section_dependencies=self.get_section_dependencies())

    def run(self):
        yield do_share_portfolio_with_spoke_task.DoSharePortfolioWithSpokeTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            puppet_account_id=self.puppet_account_id,
            sharing_mode=self.sharing_mode,
            product_generation_method=self.product_generation_method,
            organization=self.organization,
            associations=self.associations,
            launch_constraints=self.launch_constraints,
            portfolio=self.portfolio,
            region=self.region,
            account_id=self.account_id,
        )
        self.write_output(self.params_for_results_display())
