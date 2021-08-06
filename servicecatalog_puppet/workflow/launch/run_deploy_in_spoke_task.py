#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.generate import generate_shares_task
from servicecatalog_puppet.workflow.manifest import generate_manifest_with_ids_task


class RunDeployInSpokeTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return {
            f"s3.put_object_{self.puppet_account_id}": 1,
            f"s3.generate_presigned_url_{self.puppet_account_id}": 1,
            f"codebuild.start_build_{self.account_id}": 1,
        }

    def requires(self):
        return dict(
            shares=generate_shares_task.GenerateSharesTask(
                puppet_account_id=self.puppet_account_id,
                manifest_file_path=self.manifest_file_path,
                section=constants.LAUNCHES,
            ),
            new_manifest=generate_manifest_with_ids_task.GenerateManifestWithIdsTask(
                puppet_account_id=self.puppet_account_id,
                manifest_file_path=self.manifest_file_path,
            ),
        )

    def run(self):
        home_region = config.get_home_region(self.puppet_account_id)
        regions = config.get_regions(self.puppet_account_id)
        should_collect_cloudformation_events = self.should_use_sns
        should_forward_events_to_eventbridge = config.get_should_use_eventbridge(
            self.puppet_account_id
        )
        should_forward_failures_to_opscenter = config.get_should_forward_failures_to_opscenter(
            self.puppet_account_id
        )

        with self.hub_client("s3") as s3:
            bucket = f"sc-puppet-spoke-deploy-{self.puppet_account_id}"
            key = f"{os.getenv('CODEBUILD_BUILD_NUMBER', '0')}.yaml"
            s3.put_object(
                Body=self.input().get("new_manifest").open("r").read(),
                Bucket=bucket,
                Key=key,
            )
            signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=60 * 60 * 24,
            )
        with self.hub_client("ssm") as ssm:
            response = ssm.get_parameter(Name="service-catalog-puppet-version")
            version = response.get("Parameter").get("Value")
        with self.spoke_client("codebuild") as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=[
                    {"name": "VERSION", "value": version, "type": "PLAINTEXT"},
                    {"name": "MANIFEST_URL", "value": signed_url, "type": "PLAINTEXT"},
                    {
                        "name": "PUPPET_ACCOUNT_ID",
                        "value": self.puppet_account_id,
                        "type": "PLAINTEXT",
                    },
                    {"name": "HOME_REGION", "value": home_region, "type": "PLAINTEXT",},
                    {
                        "name": "REGIONS",
                        "value": ",".join(regions),
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "SHOULD_COLLECT_CLOUDFORMATION_EVENTS",
                        "value": str(should_collect_cloudformation_events),
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE",
                        "value": str(should_forward_events_to_eventbridge),
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "SHOULD_FORWARD_FAILURES_TO_OPSCENTER",
                        "value": str(should_forward_failures_to_opscenter),
                        "type": "PLAINTEXT",
                    },
                ],
            )
        self.write_output(dict(account_id=self.account_id, **response))
