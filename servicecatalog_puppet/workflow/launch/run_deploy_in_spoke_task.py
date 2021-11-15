#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.generate import generate_shares_task
from servicecatalog_puppet.workflow.manifest import generate_manifest_with_ids_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class RunDeployInSpokeTask(tasks.PuppetTask, manifest_mixin.ManifestMixen):
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
        spoke_execution_mode_deploy_env = self.spoke_execution_mode_deploy_env
        cached_config = self.manifest.get("config_cache")
        home_region = cached_config.get("home_region")
        regions = cached_config.get("regions")
        should_collect_cloudformation_events = cached_config.get(
            "should_collect_cloudformation_events"
        )
        should_forward_failures_to_opscenter = cached_config.get(
            "should_forward_failures_to_opscenter"
        )
        should_forward_events_to_eventbridge = cached_config.get(
            "should_forward_events_to_eventbridge"
        )
        version = cached_config.get("puppet_version")

        new_manifest = self.load_from_input("new_manifest")
        signed_url = new_manifest.get("signed_url")
        vars = [
            {
                "name": "SCT_CACHE_INVALIDATOR",
                "value": self.cache_invalidator,
                "type": "PLAINTEXT",
            },
            {"name": "VERSION", "value": version, "type": "PLAINTEXT"},
            {"name": "MANIFEST_URL", "value": signed_url, "type": "PLAINTEXT"},
            {
                "name": "PUPPET_ACCOUNT_ID",
                "value": self.puppet_account_id,
                "type": "PLAINTEXT",
            },
            {"name": "HOME_REGION", "value": home_region, "type": "PLAINTEXT",},
            {"name": "REGIONS", "value": ",".join(regions), "type": "PLAINTEXT",},
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
        ]
        if new_manifest.get("cached_output_signed_url"):
            vars.append(
                {
                    "name": "OUTPUT_CACHE_STARTING_POINT",
                    "value": new_manifest.get("cached_output_signed_url"),
                    "type": "PLAINTEXT",
                },
            )
        with self.spoke_client("codebuild") as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=vars,
                computeTypeOverride=spoke_execution_mode_deploy_env,
            )
        self.write_output(dict(account_id=self.account_id, **response))
