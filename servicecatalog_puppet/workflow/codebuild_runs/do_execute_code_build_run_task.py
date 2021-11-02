#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class DoExecuteCodeBuildRunTask(
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

    def api_calls_used(self):
        return [
            f"codebuild.start_build_{self.get_account_used()}_{self.project_name}",
            f"codebuild.batch_get_projects_{self.get_account_used()}_{self.project_name}",
        ]

    def requires(self):
        requirements = {
            "ssm_params": self.get_parameters_tasks(),
        }
        return requirements

    def run(self):
        with self.hub_client("codebuild") as codebuild:
            provided_parameters = self.get_parameter_values()
            parameters_to_use = list()

            projects = codebuild.batch_get_projects(names=[self.project_name]).get(
                "projects", []
            )
            for project in projects:
                if project.get("name") == self.project_name:
                    for environment_variable in project.get("environment", {}).get(
                        "environmentVariables", []
                    ):
                        if environment_variable.get("type") == "PLAINTEXT":
                            n = environment_variable.get("name")
                            if provided_parameters.get(n):
                                parameters_to_use.append(
                                    dict(
                                        name=n,
                                        value=provided_parameters.get(n),
                                        type="PLAINTEXT",
                                    )
                                )

            parameters_to_use.append(
                dict(name="TARGET_ACCOUNT_ID", value=self.account_id, type="PLAINTEXT",)
            )
            parameters_to_use.append(
                dict(name="TARGET_REGION", value=self.region, type="PLAINTEXT",)
            )
            codebuild.start_build_and_wait_for_completion(
                projectName=self.project_name,
                environmentVariablesOverride=parameters_to_use,
            )
        self.write_output(self.params_for_results_display())
