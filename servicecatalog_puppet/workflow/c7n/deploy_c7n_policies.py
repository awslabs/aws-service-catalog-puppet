#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from datetime import datetime

import luigi

from servicecatalog_puppet import constants, serialisation_utils
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
        member_role = "arn:aws:iam::{account_id}:role" + self.role_path + self.role_name
        for policy in unwrap(self.policies):
            policy["mode"]["type"] = "cloudtrail"
            policy["mode"]["member-role"] = member_role
            policies.append(policy)

        bucket = f"sc-puppet-c7n-artifacts-{self.account_id}-{self.region}"
        key = str(datetime.now())

        with self.spoke_regional_client("s3") as s3:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=serialisation_utils.dump(unwrap(dict(policies=policies))),
            )
            cached_output_signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=60 * 60 * 24,
            )
        policies_file_url = cached_output_signed_url
        custodian_role_arn = (
            f"arn:aws:iam::{self.account_id}:role" + self.role_path + self.role_name
        )
        regions_to_run_in = list(self.deployments.keys())
        parameters_to_use = [
            dict(name="POLICIES_FILE_URL", value=policies_file_url, type="PLAINTEXT",),
            dict(name="REGIONS", value=" ".join(regions_to_run_in), type="PLAINTEXT",),
            dict(
                name="CUSTODIAN_ROLE_ARN", value=custodian_role_arn, type="PLAINTEXT",
            ),
        ]

        with self.spoke_client("codebuild") as codebuild:
            result = codebuild.start_build_and_wait_for_completion(
                projectName="servicecatalog-puppet-deploy-c7n",
                environmentVariablesOverride=parameters_to_use,
            )
            if result.get("buildStatus") != "SUCCEEDED":
                raise Exception(f"Deploying policy failed: {result.get('buildStatus')}")

        self.write_empty_output()
