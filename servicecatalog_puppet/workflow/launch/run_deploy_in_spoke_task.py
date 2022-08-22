#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import yaml_utils
from servicecatalog_puppet import environmental_variables
from servicecatalog_puppet import environmental_variables_parameters
from servicecatalog_puppet import constants

from servicecatalog_puppet.workflow.dependencies import tasks


class RunDeployInSpokeTask(tasks.TaskWithReference):
    task_reference = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    generate_manifest_ref = luigi.Parameter()

    home_region = environmental_variables_parameters.environmentalParams().home_region
    regions = environmental_variables_parameters.environmentalParams().regions

    should_collect_cloudformation_events = (
        environmental_variables_parameters.environmentalParams().should_collect_cloudformation_events
    )
    should_forward_events_to_eventbridge = (
        environmental_variables_parameters.environmentalParams().should_forward_events_to_eventbridge
    )
    should_forward_failures_to_opscenter = (
        environmental_variables_parameters.environmentalParams().should_forward_failures_to_opscenter
    )
    version = environmental_variables_parameters.environmentalParams().version

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
        generated_manifest = self.get_output_from_reference_dependency(
            self.generate_manifest_ref
        )
        reference_signed_url = generated_manifest.get("reference_signed_url")
        manifest_signed_url = generated_manifest.get("manifest_signed_url")
        cached_output_signed_url = generated_manifest.get("cached_output_signed_url")

        vars = [
            {
                "name": environmental_variables.CACHE_INVALIDATOR,
                "value": self.cache_invalidator,
                "type": "PLAINTEXT",
            },
            {"name": "VERSION", "value": self.version, "type": "PLAINTEXT"},
            {"name": "MANIFEST_URL", "value": manifest_signed_url, "type": "PLAINTEXT"},
            {"name": "TASK_REFERENCE_URL", "value": reference_signed_url, "type": "PLAINTEXT"},
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
            {
                "name": "OUTPUT_CACHE_STARTING_POINT",
                "value": cached_output_signed_url,
                "type": "PLAINTEXT",
            },
        ]

        if "http" in self.version:
            install_command = f"pip install {self.version}"
        else:
            install_command = (
                f"pip install aws-service-catalog-puppet=={self.version}",
            )

        build_spec = yaml_utils.dump(
            dict(
                version="0.2",
                phases=dict(
                    install={
                        "runtime-versions": dict(python=3.7),
                        "commands": ["echo $VERSION", install_command],
                    },
                    build=dict(
                        commands=[
                            "curl $TASK_REFERENCE_URL > manifest-task-reference-full.yaml",
                            "curl $MANIFEST_URL > manifest-expanded.yaml",
                            """servicecatalog-puppet --info deploy-from-task-reference \
                      --execution-mode spoke \
                      --puppet-account-id $PUPPET_ACCOUNT_ID \
                      --single-account $(aws sts get-caller-identity --query Account --output text) \
                      --home-region $HOME_REGION \
                      --regions $REGIONS \
                      --should-collect-cloudformation-events $SHOULD_COLLECT_CLOUDFORMATION_EVENTS \
                      --should-forward-events-to-eventbridge $SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE \
                      --should-forward-failures-to-opscenter $SHOULD_FORWARD_FAILURES_TO_OPSCENTER \
                      manifest-task-reference-full.yaml""",
                        ]
                    ),
                ),
                artifacts=dict(
                    files=["results/*/*", "output/*/*"], name="DeployInSpokeProject"
                ),
            )
        )

        uiq = "aaa"
        # bucket_to_use = ""

        artifacts_override = {
            "type": "S3",
            # 'location': bucket_to_use,
            "path": "spoke-execution-results",
            "namespaceType": "NONE",
            "name": f"{uiq}-{self.account_id}",
            "packaging": "ZIP",
            "artifactIdentifier": "DeployInSpokeProject",
            "bucketOwnerAccess": "FULL",
        }

        with self.spoke_client("codebuild") as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=vars,
                computeTypeOverride=self.spoke_execution_mode_deploy_env,
                buildspecOverride=build_spec,
                # artifactsOverride=artifacts_override,
            )
        self.write_output(dict(account_id=self.account_id, **response))
