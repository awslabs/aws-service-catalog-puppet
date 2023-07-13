#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import glob
import os
import zipfile

from servicecatalog_puppet import (
    config,
    constants,
    environmental_variables,
    serialisation_utils,
    task_reference_constants,
)
from servicecatalog_puppet.workflow.dependencies import tasks


class GenerateManifestWithIdsTask(tasks.TaskWithReference):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
        }

    cachable_level = constants.CACHE_LEVEL_NO_CACHE

    def run(self):
        bucket = f"sc-puppet-spoke-deploy-{self.puppet_account_id}"

        with zipfile.ZipFile(
            "output/GetSSMParamTask.zip", "w", zipfile.ZIP_DEFLATED
        ) as zip:
            files = list()
            files.extend(glob.glob(f"output/*/**", recursive=True))
            for filename in files:
                zip.write(filename, filename)
            for f in glob.glob(f"{self.manifest_files_path}/tasks/*"):
                zip.write(f, f"tasks/{os.path.basename(f)}")

        with self.hub_client("s3") as s3:
            key = f"{os.getenv('CODEBUILD_BUILD_NUMBER', '0')}-cached-output.zip"
            s3.upload_file(
                Filename="output/GetSSMParamTask.zip", Bucket=bucket, Key=key,
            )
            cached_output_signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=60 * 60 * 24,
            )

        with self.hub_client("s3") as s3:
            (
                reference_signed_url,
                reference_task_reference_content,
            ) = self.get_signed_url_for_task_reference(bucket, s3)
            (manifest_signed_url, manifest_content,) = self.get_signed_url_for_manifest(
                bucket, s3
            )

        version = constants.VERSION
        home_region = constants.HOME_REGION

        vars = [
            {
                "name": environmental_variables.DRIFT_TOKEN,
                "value": self.drift_token,
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.RUN_TOKEN,
                "value": self.run_token,
                "type": "PLAINTEXT",
            },
            {"name": "VERSION", "value": version, "type": "PLAINTEXT"},
            {"name": "MANIFEST_URL", "value": manifest_signed_url, "type": "PLAINTEXT"},
            # {
            #     "name": "TASK_REFERENCE_URL",
            #     "value": reference_signed_url,
            #     "type": "PLAINTEXT",
            # },
            {
                "name": "PUPPET_ACCOUNT_ID",
                "value": self.puppet_account_id,
                "type": "PLAINTEXT",
            },
            {"name": "HOME_REGION", "value": home_region, "type": "PLAINTEXT",},
            {
                "name": "REGIONS",
                "value": ",".join(config.get_regions()),
                "type": "PLAINTEXT",
            },
            {
                "name": "SHOULD_COLLECT_CLOUDFORMATION_EVENTS",
                "value": str(config.get_should_use_sns()),
                "type": "PLAINTEXT",
            },
            {
                "name": "SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE",
                "value": str(config.get_should_use_eventbridge()),
                "type": "PLAINTEXT",
            },
            {
                "name": "SHOULD_FORWARD_FAILURES_TO_OPSCENTER",
                "value": str(config.get_should_forward_failures_to_opscenter()),
                "type": "PLAINTEXT",
            },
            {
                "name": "OUTPUT_CACHE_STARTING_POINT",
                "value": cached_output_signed_url,
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.IS_CACHING_ENABLED,
                "value": "False",  # no caching in spokes
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.INITIALISER_STACK_TAGS,
                "value": config.get_initialiser_stack_tags(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.GLOBAL_SHARING_MODE,
                "value": config.get_global_sharing_mode_default(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS,
                "value": config.get_should_delete_rollback_complete_stacks(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.SHOULD_USE_PRODUCT_PLANS,
                "value": config.get_should_use_product_plans(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.SPOKE_EXECUTION_MODE_DEPLOY_ENV,
                "value": config.get_spoke_execution_mode_deploy_env(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.SCHEDULER_THREADS_OR_PROCESSES,
                "value": config.get_spoke_scheduler_threads_or_processes(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.SCHEDULER_ALGORITHM,
                "value": config.get_spoke_scheduler_algorithm(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.GLOBAL_SHARE_TAG_OPTIONS,
                "value": config.get_global_share_tag_options_default(),
                "type": "PLAINTEXT",
            },
            {
                "name": environmental_variables.GLOBAL_SHARE_PRINCIPALS,
                "value": config.get_global_share_principals_default(),
                "type": "PLAINTEXT",
            },
        ]

        if "http" in version:
            install_command = f"pip install {version}"
        else:
            install_command = f"pip install aws-service-catalog-puppet=={version}"

        build_spec = constants.RUN_DEPLOY_IN_SPOKE_BUILDSPEC.format(install_command)

        self.write_output(
            dict(
                # reference_task_reference_content=reference_task_reference_content,
                # reference_signed_url=reference_signed_url,
                cached_output_signed_url=cached_output_signed_url,
                manifest_signed_url=manifest_signed_url,
                manifest_content=manifest_content,
                build_spec=build_spec,
                spoke_execution_mode_deploy_env=self.spoke_execution_mode_deploy_env,
                vars=vars,
            )
        )

    def get_signed_url_for_task_reference(self, bucket, s3):
        task_reference_content = open(
            self.manifest_task_reference_file_path.replace(".json", "-full.json"), "r",
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
        key = f"{os.getenv('CODEBUILD_BUILD_NUMBER', '0')}-reference.json"
        self.debug(f"Uploading task reference {key} to {bucket}")
        s3.put_object(
            Body=task_reference_content, Bucket=bucket, Key=key,
        )
        self.debug(f"Generating presigned URL for {key}")
        signed_url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=60 * 60 * 24,
        )
        return signed_url, task_reference_content

    def get_signed_url_for_manifest(self, bucket, s3):
        task_reference_content = open(
            f"{self.manifest_files_path}/manifest-expanded.yaml", "r",
        ).read()
        key = f"{os.getenv('CODEBUILD_BUILD_NUMBER', '0')}-manifest.yaml"
        self.debug(f"Uploading manifest {key} to {bucket}")
        s3.put_object(
            Body=task_reference_content, Bucket=bucket, Key=key,
        )
        self.debug(f"Generating presigned URL for {key}")
        signed_url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=60 * 60 * 24,
        )
        return signed_url, task_reference_content
