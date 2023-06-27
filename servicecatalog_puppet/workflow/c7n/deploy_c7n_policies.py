#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants, serialisation_utils, config
from servicecatalog_puppet.serialisation_utils import unwrap
from servicecatalog_puppet.workflow.dependencies import tasks


class DeployC7NPolicies(tasks.TaskWithReferenceAndCommonParameters):
    role_name = luigi.Parameter()
    role_path = luigi.Parameter()
    policies = luigi.ListParameter()
    deployments = luigi.DictParameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
        }

    def run(self):
        policies = list()
        partition = config.get_partition()
        member_role = (
            "arn:"
            + partition
            + ":iam::{account_id}:role"
            + self.role_path
            + self.role_name
        )
        for policy in unwrap(self.policies):
            if policy.get("mode", {}).get("type") == "cloudtrail":
                policy["mode"]["member-role"] = member_role
            policies.append(policy)

        bucket = f"sc-puppet-c7n-artifacts-{self.account_id}-{self.region}"
        key = "latest"

        with self.spoke_regional_client("s3") as s3:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=serialisation_utils.dump(unwrap(dict(policies=policies))),
            )
        custodian_role_arn = (
            f"arn:{partition}:iam::{self.account_id}:role"
            + self.role_path
            + self.role_name
        )
        regions_to_run_in = list(self.deployments.keys())

        with self.spoke_client("ssm") as ssm:
            ssm.put_parameter(
                Name="/servicecatalog-puppet/aws-c7n-lambdas/REGIONS",
                Value=" ".join(regions_to_run_in),
                Type="String",
                Overwrite=True,
            )
            ssm.put_parameter(
                Name="/servicecatalog-puppet/aws-c7n-lambdas/CUSTODIAN_ROLE_ARN",
                Value=custodian_role_arn,
                Type="String",
                Overwrite=True,
            )
        with self.spoke_client("codebuild") as codebuild:
            result = codebuild.start_build_and_wait_for_completion(
                projectName="servicecatalog-puppet-deploy-c7n",
            )
            if result.get("buildStatus") != "SUCCEEDED":
                raise Exception(f"Deploying policy failed: {result.get('buildStatus')}")

        self.write_empty_output()
