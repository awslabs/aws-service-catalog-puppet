#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os

import botocore
import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class GetCloudFormationTemplateFromS3(tasks.TaskWithReference):
    account_id = luigi.Parameter()

    bucket = luigi.Parameter()
    key = luigi.Parameter()
    region = luigi.Parameter()
    version_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "bucket": self.bucket,
            "key": self.key.replace("-${AWS::Region}", f"-{self.region}"),
            "region": self.region,
            "version_id": self.version_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        with self.hub_client("s3") as s3:
            regional_template = self.key.replace("-${AWS::Region}", f"-{self.region}")
            global_template = self.key.replace("-${AWS::Region}", "")
            p = dict(Bucket=self.bucket)
            if self.version_id != "":
                p["VersionId"] = self.version_id

            self.info(f"Trying regional template: {regional_template}")
            output = self.output_location
            if not os.path.exists(os.path.dirname(output)):
                os.makedirs(os.path.dirname(output))

            try:
                s3.download_file(Key=regional_template, Filename=output, **p)
            except botocore.exceptions.ClientError as e:
                if "404" == str(e.response["Error"]["Code"]):
                    self.info(
                        f"Didnt find regional template: {regional_template}, will try global: {global_template}"
                    )
                    s3.download_file(Key=global_template, Filename=output, **p)
                else:
                    raise e
