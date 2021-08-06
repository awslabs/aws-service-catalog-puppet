#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import tasks


class PortfolioManagementTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()
