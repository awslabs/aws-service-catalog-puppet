#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import glob
import os
import zipfile

from servicecatalog_puppet.workflow.dependencies import tasks
from luigi.contrib.s3 import S3Target


class GenerateManifestWithIdsTask(tasks.TaskWithReference):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def download_all_cached_tasks_outputs(self):
        for task_reference, output in self.input().get("reference_dependencies", {}).items():
            if isinstance(output, S3Target):
                s3_url = output.path.split("/")
                bucket = s3_url[2]
                key = "/".join(s3_url[3:])
                target = ".".join(key.split(".")[0:-1])
                target_dir = target.replace('/latest.json', '')
                # target = key
                print("STARTING THIS")
                print("STARTING THIS")
                print("STARTING THIS")
                print("STARTING THIS")
                print("STARTING THIS")
                print("STARTING THIS")
                print("STARTING THIS")
                print(f"1Checking for {target_dir}")
                if not os.path.exists(target_dir):
                    print("MADE PARENT DIR")
                    os.makedirs(target_dir)
                print(f"2CHECKING FOR {target}")
                print(f"might be Downloading {bucket} {key} to {target}")
                if not os.path.exists(target):
                    print("downloading it")
                    with self.hub_client('s3') as s3:
                        s3.download_file(Bucket=bucket, Key=key, Filename=target)
                print("")
                print("")
                print("")

    def run(self):
        self.download_all_cached_tasks_outputs()

        bucket = f"sc-puppet-spoke-deploy-{self.puppet_account_id}"

        with zipfile.ZipFile(
            "output/GetSSMParamTask.zip", "w", zipfile.ZIP_DEFLATED
        ) as zip:
            files = list()
            files.extend(glob.glob(f"output/*/**", recursive=True))
            for filename in files:
                zip.write(filename, filename)

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
            self.manifest_task_reference_file_path.replace(
                "task-reference.yaml", "task-reference-filtered.yaml"
            ),
            "r",
        ).read()
        key = f"{os.getenv('CODEBUILD_BUILD_NUMBER', '0')}-reference.yaml"
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
            self.manifest_task_reference_file_path.replace(
                "task-reference.yaml", "expanded.yaml"
            ),
            "r",
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
