#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import io
import zipfile

import luigi

from servicecatalog_puppet import config, constants, serialisation_utils
from servicecatalog_puppet.serialisation_utils import unwrap
from servicecatalog_puppet.workflow.dependencies import tasks


class DeployC7NPolicies(tasks.TaskWithReferenceAndCommonParameters):
    role_name = luigi.Parameter()
    role_path = luigi.Parameter()
    policies = luigi.ListParameter()
    deployments = luigi.DictParameter()
    uses_orgs = luigi.BoolParameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
        }

    def generate_policies(self, partition):
        policies = list()
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
        return serialisation_utils.dump(unwrap(dict(policies=policies)))

    def generate_accounts(self, partition):
        accounts = dict()
        for deployment_region, deployment_accounts in self.deployments.items():
            for deployment_account_id in deployment_accounts:
                if accounts.get(deployment_account_id) is None:
                    accounts[deployment_account_id] = []
                accounts[deployment_account_id].append(deployment_region)

        result = []
        for account_id, regions in accounts.items():
            result.append(
                {
                    "account_id": account_id,
                    "name": str(account_id),
                    "regions": regions,
                    "role": f"arn:{partition}:iam::{account_id}:role{self.role_path}{self.role_name}",
                }
            )

        return serialisation_utils.dump(unwrap(dict(accounts=result)))

    def run(self):
        partition = config.get_partition()
        policies = self.generate_policies(partition)
        accounts = self.generate_accounts(partition)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr("accounts.yaml", accounts)
            zip_file.writestr("policies.yaml", policies)

            # ('2.txt', io.BytesIO(b'222'))]:

        bucket = f"sc-puppet-c7n-artifacts-{self.account_id}-{self.region}"
        key = "latest"

        with self.spoke_regional_client("s3") as s3:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=zip_buffer.getvalue(),
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
