#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import environmental_variables
from servicecatalog_puppet import environmental_variables_parameters
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.manifest import generate_manifest_with_ids_task


from servicecatalog_puppet.workflow.dependencies import tasks


class RunDeployInSpokeTask(tasks.TaskWithReference):
    task_reference = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()

    home_region = environmental_variables_parameters.environmentalParams().home_region
    regions = environmental_variables_parameters.environmentalParams().regions

    should_collect_cloudformation_events = environmental_variables_parameters.environmentalParams().should_collect_cloudformation_events
    should_forward_events_to_eventbridge = environmental_variables_parameters.environmentalParams().should_forward_events_to_eventbridge
    should_forward_failures_to_opscenter = environmental_variables_parameters.environmentalParams().should_forward_failures_to_opscenter

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return {
            f"codebuild.start_build_{self.account_id}": 1,
        }

    def run(self):
        version = ""
        signed_url = ""

        # home_region = cached_config.get("home_region")
        # regions = cached_config.get("regions")
        # should_collect_cloudformation_events = cached_config.get(
        #     "should_collect_cloudformation_events"
        # )
        # should_forward_failures_to_opscenter = cached_config.get(
        #     "should_forward_failures_to_opscenter"
        # )
        # should_forward_events_to_eventbridge = cached_config.get(
        #     "should_forward_events_to_eventbridge"
        # )
        # version = cached_config.get("puppet_version")




        # new_manifest = self.load_from_input("new_manifest")
        # signed_url = new_manifest.get("signed_url")
        vars = [
            {
                "name": environmental_variables.CACHE_INVALIDATOR,
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
            {"name": "HOME_REGION", "value": self.home_region, "type": "PLAINTEXT",},
            {"name": "REGIONS", "value": ",".join(self.regions), "type": "PLAINTEXT",},
            {
                "name": "SHOULD_COLLECT_CLOUDFORMATION_EVENTS",
                "value": str(self.should_collect_cloudformation_events),
                "type": "PLAINTEXT",
            },
            {
                "name": "SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE",
                "value": str(self.should_forward_events_to_eventbridge),
                "type": "PLAINTEXT",
            },
            {
                "name": "SHOULD_FORWARD_FAILURES_TO_OPSCENTER",
                "value": str(self.should_forward_failures_to_opscenter),
                "type": "PLAINTEXT",
            },
        ]
        # if new_manifest.get("cached_output_signed_url"):
        #     vars.append(
        #         {
        #             "name": "OUTPUT_CACHE_STARTING_POINT",
        #             "value": new_manifest.get("cached_output_signed_url"),
        #             "type": "PLAINTEXT",
        #         },
        #     )
        with self.spoke_client("codebuild") as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=vars,
                computeTypeOverride=self.spoke_execution_mode_deploy_env,
            )
        self.write_output(dict(account_id=self.account_id, **response))
