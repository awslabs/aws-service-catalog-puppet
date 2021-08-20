#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import io
import json
import zipfile

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.general import get_ssm_param_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.workspaces import Limits
from servicecatalog_puppet.workflow.workspaces import prepare_account_for_workspace_task
from servicecatalog_puppet.workflow.workspaces import workspace_base_task


class ProvisionWorkspaceTask(
    workspace_base_task.WorkspaceBaseTask,
    get_ssm_param_task.PuppetTaskWithParameters,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    workspace_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    bucket = luigi.Parameter()
    key = luigi.Parameter()
    version_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    execution = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "workspace_name": self.workspace_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = {
            "section_dependencies": self.get_section_dependencies(),
            "ssm_params": self.get_parameters_tasks(),
        }
        if not self.is_running_in_spoke():
            requirements[
                "account_ready"
            ] = prepare_account_for_workspace_task.PrepareAccountForWorkspaceTask(
                puppet_account_id=self.puppet_account_id, account_id=self.account_id,
            )
        return requirements

    def resources_used(self):
        return [
            (self.account_id, Limits.CODEBUILD_CONCURRENT_PROJECTS),
        ]

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

        options = json.loads(options)

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

            build = codebuild.start_build_and_wait_for_completion(
                projectName=constants.EXECUTE_TERRAFORM_PROJECT_NAME,
                environmentVariablesOverride=parameters_to_use,
            )

        if len(self.ssm_param_outputs) > 0:
            with self.spoke_client("s3") as s3:
                output_bucket = f"sc-puppet-state-{self.account_id}"
                output_key = f"terraform-executions/{build.get('id').split(':')[1]}/artifacts-execute/outputs.json"
                outputs = json.loads(
                    s3.get_object(Bucket=output_bucket, Key=output_key)
                    .get("Body")
                    .read()
                )

                for ssm_param_output in self.ssm_param_outputs:
                    self.info(
                        f"writing SSM Param: {ssm_param_output.get('stack_output')}"
                    )
                    with self.hub_client("ssm") as ssm:
                        if outputs.get(ssm_param_output.get("stack_output")):
                            output_value = outputs.get(
                                ssm_param_output.get("stack_output")
                            ).get("value")

                            ssm_parameter_name = ssm_param_output.get("param_name")
                            ssm_parameter_name = ssm_parameter_name.replace(
                                "${AWS::Region}", self.region
                            )
                            ssm_parameter_name = ssm_parameter_name.replace(
                                "${AWS::AccountId}", self.account_id
                            )
                            ssm.put_parameter_and_wait(
                                Name=ssm_parameter_name,
                                Value=output_value,
                                Type=ssm_param_output.get("param_type", "String"),
                                Overwrite=True,
                            )
                        else:
                            raise Exception(
                                f"Could not find {ssm_param_output.get('stack_output')} in the outputs"
                            )

        self.write_output(self.params_for_results_display())
