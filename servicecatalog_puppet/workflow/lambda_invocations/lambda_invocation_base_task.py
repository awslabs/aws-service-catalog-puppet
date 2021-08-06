#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks


class LambdaInvocationBaseTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.LAMBDA_INVOCATIONS

    @property
    def item_name(self):
        return self.lambda_invocation_name

    @property
    def item_identifier(self):
        return "lambda_invocation_name"
