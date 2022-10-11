#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import io
import json
from servicecatalog_puppet import serialisation_utils
import zipfile

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class TerminateWorkspaceTask(tasks.TaskWithParameters):
    workspace_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    bucket = luigi.Parameter()
    key = luigi.Parameter()
    version_id = luigi.Parameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    execution = luigi.Parameter()
    manifest_file_path = luigi.Parameter()

    section_name = constants.WORKSPACES

    @property
    def item_name(self):
        return self.workspace_name

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "workspace_name": self.workspace_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        with self.hub_client("s3") as s3:
            options = (
                zipfile.ZipFile(
                    io.BytesIO(
                        s3.get_object(Bucket=self.bucket, Key=self.key)
                        .get("Body")
                        .read()
                    )
                )
                .open(f"options.json", "r")
                .read()
            )

        options = serialisation_utils.json_loads(options)

        zip_file_path = f"s3://{self.bucket}/{self.key}"
        state_file_path = f"s3://sc-puppet-state-{self.account_id}/workspace/{self.workspace_name}/{self.account_id}/{self.region}.zip"
        with self.spoke_client("codebuild") as codebuild:
            parameters_to_use = [
                dict(name="TARGET_ACCOUNT", value=self.account_id, type="PLAINTEXT",),
                dict(name="STATE_FILE", value=state_file_path, type="PLAINTEXT",),
                dict(name="ZIP", value=zip_file_path, type="PLAINTEXT",),
            ]

            for parameter_name, parameter_value in self.get_parameter_values().items():
                parameters_to_use.append(
                    dict(
                        name=f"TF_VAR_{parameter_name}",
                        value=f"{parameter_value}",
                        type="PLAINTEXT",
                    ),
                )

            parameters_to_use.append(
                dict(
                    name="TERRAFORM_VERSION",
                    value=options.get("Terraform", {}).get(
                        "Version", constants.DEFAULT_TERRAFORM_VERSION_VALUE
                    ),
                    type="PLAINTEXT",
                ),
            )

            codebuild.start_build_and_wait_for_completion(
                projectName=constants.TERMINATE_TERRAFORM_PROJECT_NAME,
                environmentVariablesOverride=parameters_to_use,
            )

        self.write_empty_output()
