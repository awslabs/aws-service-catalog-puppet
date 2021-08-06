#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class SpokeLocalPortfolioBaseTask(tasks.PuppetTask, manifest_mixin.ManifestMixen):
    manifest_file_path = luigi.Parameter()

    @property
    def status(self):
        return (
            self.manifest.get(self.section_name)
            .get(self.spoke_local_portfolio_name)
            .get("status", constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED)
        )

    @property
    def section_name(self):
        return constants.SPOKE_LOCAL_PORTFOLIOS

    @property
    def item_name(self):
        return self.spoke_local_portfolio_name

    @property
    def item_identifier(self):
        return "spoke_local_portfolio_name"
