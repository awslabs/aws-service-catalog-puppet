#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import glob
import os
import zipfile

from servicecatalog_puppet.workflow.dependencies import tasks


class GenerateManifestWithIdsTask(tasks.TaskWithReference):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

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

        self.write_output(
            dict(
                reference_task_reference_content=reference_task_reference_content,
                reference_signed_url=reference_signed_url,
                cached_output_signed_url=cached_output_signed_url,
                manifest_signed_url=manifest_signed_url,
                manifest_content=manifest_content,
            )
        )

    def get_signed_url_for_task_reference(self, bucket, s3):
        task_reference_content = open(
            self.manifest_task_reference_file_path.replace(".json", "-full.json"), "r",
        ).read()
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
