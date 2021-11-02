#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks as workflow_tasks


class AssertionBaseTask(workflow_tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.ASSERTIONS

    @property
    def item_name(self):
        return self.assertion_name

    @property
    def item_identifier(self):
        return "assertion_name"
