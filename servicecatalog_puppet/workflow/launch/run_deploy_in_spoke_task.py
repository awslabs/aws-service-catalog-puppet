#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi
import os

from servicecatalog_puppet import (
    constants,
    serialisation_utils,
    task_reference_constants,
)
from servicecatalog_puppet.workflow.dependencies import tasks


class RunDeployInSpokeTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    generate_manifest_ref = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_NO_CACHE

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
        }

    def run(self):
        generated_manifest = self.get_output_from_reference_dependency(
            self.generate_manifest_ref
        )
        build_spec = generated_manifest.get("build_spec")
        spoke_execution_mode_deploy_env = generated_manifest.get(
            "spoke_execution_mode_deploy_env"
        )
        vars = generated_manifest.get("vars")

        bucket = f"sc-puppet-spoke-deploy-{self.puppet_account_id}"
        with self.hub_client("s3") as s3:
            task_reference_content = open(
                self.manifest_task_reference_file_path.replace(".json", "-full.json"),
                "r",
            ).read()
            task_reference = serialisation_utils.load_as_json(task_reference_content)
            for task_ref, task in task_reference.get("all_tasks", {}).items():
                for a in [
                    task_reference_constants.MANIFEST_SECTION_NAMES,
                    task_reference_constants.MANIFEST_ITEM_NAMES,
                ]:
                    if task.get(a):
                        del task_reference["all_tasks"][task_ref][a]
            task_reference_content = serialisation_utils.dump_as_json(task_reference)
            key = f"{os.getenv('CODEBUILD_BUILD_NUMBER', '0')}-reference-for-{self.account_id}.json"
            self.debug(f"Uploading task reference {key} to {bucket}")
            s3.put_object(
                Body=task_reference_content, Bucket=bucket, Key=key,
            )
            self.debug(f"Generating presigned URL for {key}")
            reference_signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=60 * 60 * 24,
            )
            vars.append(
                {
                    "name": "TASK_REFERENCE_URL",
                    "value": reference_signed_url,
                    "type": "PLAINTEXT",
                },
            )

        with self.spoke_client("codebuild") as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=vars,
                computeTypeOverride=spoke_execution_mode_deploy_env,
                buildspecOverride=build_spec,
                imageOverride=constants.CODEBUILD_DEFAULT_IMAGE,
            )
        self.write_output(dict(account_id=self.account_id, **response))
