#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_base_task
from servicecatalog_puppet.workflow.codebuild_runs import execute_code_build_run_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class CodeBuildRunForTask(
    code_build_run_base_task.CodeBuildRunBaseTask, manifest_mixin.ManifestMixen
):
    code_build_run_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "code_build_run_name": self.code_build_run_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return execute_code_build_run_task.ExecuteCodeBuildRunTask

    def run(self):
        self.write_output(self.params_for_results_display())
