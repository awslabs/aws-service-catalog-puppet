#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_base_task
from servicecatalog_puppet.workflow.codebuild_runs import do_execute_code_build_run_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class ExecuteCodeBuildRunTask(
    code_build_run_base_task.CodeBuildRunBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    code_build_run_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    execution = luigi.Parameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    project_name = luigi.Parameter()
    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "code_build_run_name": self.code_build_run_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(section_dependencies=self.get_section_dependencies())

    def run(self):
        yield do_execute_code_build_run_task.DoExecuteCodeBuildRunTask(
            manifest_file_path=self.manifest_file_path,
            code_build_run_name=self.code_build_run_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            account_id=self.account_id,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            project_name=self.project_name,
            requested_priority=self.requested_priority,
            execution=self.execution,
        )
        self.write_output(self.params_for_results_display())
