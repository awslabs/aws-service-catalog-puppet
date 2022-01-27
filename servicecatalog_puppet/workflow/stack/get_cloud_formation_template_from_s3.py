#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import tasks


class GetCloudFormationTemplateFromS3(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    bucket = luigi.Parameter()
    key = luigi.Parameter()
    region = luigi.Parameter()
    version_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "bucket": self.bucket,
            "key": self.key,
            "region": self.region,
            "version_id": self.version_id,
        }

    def run(self):
        with self.hub_client("s3") as s3:
            regional_template = self.key.replace("-${AWS::Region}", f"-{self.region}")
            global_template = self.key.replace("-${AWS::Region}", "")
            p = dict(Bucket=self.bucket)
            if self.version_id != "":
                p["VersionId"] = self.version_id

            self.debug(f"Trying regional template: {regional_template}")
            try:
                response = s3.get_object(Key=regional_template, **p)
            except s3.exceptions.NoSuchKey:
                self.debug(f"Didnt find regional template: {regional_template}")
                response = s3.get_object(Key=global_template, **p)
            self.write_output(
                response.get("Body").read().decode("utf8"), skip_json_dump=True
            )
