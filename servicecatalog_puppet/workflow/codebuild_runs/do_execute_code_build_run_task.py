#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class DoExecuteCodeBuildRunTask(tasks.TaskWithParameters):
    code_build_run_name = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    project_name = luigi.Parameter()

    manifest_file_path = luigi.Parameter()

    section_name = constants.CODE_BUILD_RUNS
    cachable_level = constants.CACHE_LEVEL_RUN

    @property
    def item_name(self):
        return self.code_build_run_name

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "code_build_run_name": self.code_build_run_name,
            "region": self.region,
            "account_id": self.account_id,
        }

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
            result = codebuild.start_build_and_wait_for_completion(
                projectName=self.project_name,
                environmentVariablesOverride=parameters_to_use,
            )
            if result.get("buildStatus") != "SUCCEEDED":
                raise Exception(
                    f"Executing CodeBuild failed: {result.get('buildStatus')}"
                )
        self.write_empty_output()
