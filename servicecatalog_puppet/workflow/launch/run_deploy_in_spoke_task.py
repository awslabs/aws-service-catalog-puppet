#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet import environmental_variables
from servicecatalog_puppet.workflow.dependencies import tasks


class RunDeployInSpokeTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    generate_manifest_ref = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        generated_manifest = self.get_output_from_reference_dependency(
            self.generate_manifest_ref
        )
        reference_signed_url = generated_manifest.get("reference_signed_url")
        manifest_signed_url = generated_manifest.get("manifest_signed_url")
        cached_output_signed_url = generated_manifest.get("cached_output_signed_url")

        version = constants.VERSION
        home_region = constants.HOME_REGION

        vars = [
            {
                "name": environmental_variables.CACHE_INVALIDATOR,
                "value": self.cache_invalidator,
                "type": "PLAINTEXT",
            },
            {"name": "VERSION", "value": version, "type": "PLAINTEXT"},
            {"name": "MANIFEST_URL", "value": manifest_signed_url, "type": "PLAINTEXT"},
            {
                "name": "TASK_REFERENCE_URL",
                "value": reference_signed_url,
                "type": "PLAINTEXT",
            },
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
                "value": config.get_scheduler_threads_or_processes(),
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

        with self.spoke_client("codebuild") as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=vars,
                computeTypeOverride=self.spoke_execution_mode_deploy_env,
                buildspecOverride=build_spec,
            )
        self.write_output(dict(account_id=self.account_id, **response))
