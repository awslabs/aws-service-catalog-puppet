#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class RunDeployInSpokeTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    generate_manifest_ref = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_LOW

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
        }

    def run(self):
        generated_manifest = self.get_output_from_reference_dependency(
            self.generate_manifest_ref
        )
        build_spec = generated_manifest.get("build_spec")
        spoke_execution_mode_deploy_env = generated_manifest.get(
            "spoke_execution_mode_deploy_env"
        )
        vars = generated_manifest.get("vars")

        with self.spoke_client("codebuild") as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=vars,
                computeTypeOverride=spoke_execution_mode_deploy_env,
                buildspecOverride=build_spec,
            )
        self.write_output(dict(account_id=self.account_id, **response))
