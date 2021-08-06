#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.lambda_invocations import invoke_lambda_task
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_base_task,
)
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class LambdaInvocationForTask(
    lambda_invocation_base_task.LambdaInvocationBaseTask, manifest_mixin.ManifestMixen
):
    lambda_invocation_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return invoke_lambda_task.InvokeLambdaTask

    def run(self):
        self.write_output(self.params_for_results_display())
