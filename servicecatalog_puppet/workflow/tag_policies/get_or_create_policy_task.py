#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from servicecatalog_puppet import serialisation_utils

import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class GetOrCreatePolicyTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    policy_name = luigi.Parameter()
    policy_description = luigi.Parameter()
    policy_content = luigi.DictParameter()
    tags = luigi.ListParameter()

    manifest_file_path = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "policy_name": self.policy_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        with self.organizations_policy_client() as orgs:
            if self.policy_content.get("default") is not None:
                unwrapped = tasks.unwrap(self.policy_content.get("default"))
            elif self.policy_content.get("s3") is not None:
                with self.spoke_client("s3") as s3:
                    bucket = self.policy_content.get("s3").get("bucket")
                    key = self.policy_content.get("s3").get("key")
                    unwrapped = s3.get_object(Bucket=bucket, Key=key).read()
            else:
                raise Exception("Not supported policy content structure")

            content = json.dumps(unwrapped, indent=0, default=str)
            tags = [dict(Key="ServiceCatalogPuppet:Actor", Value="generated")]
            for tag in self.tags:
                tags.append(dict(Key=tag.get("Key"), Value=tag.get("Value")))

            paginator = orgs.get_paginator("list_policies")
            for page in paginator.paginate(Filter="TAG_POLICY"):
                for policy in page.get("Policies", []):
                    if policy.get("Name") == self.policy_name:
                        kwargs = dict(PolicyId=policy.get("Id"))

                        if policy.get("Description") != self.policy_description:
                            kwargs["Description"] = self.policy_description

                        remote_policy_content = (
                            orgs.describe_policy(PolicyId=policy.get("Id"))
                            .get("Policy")
                            .get("Content")
                        )

                        if unwrapped != serialisation_utils.json_loads(
                            remote_policy_content
                        ):
                            kwargs["Content"] = content

                        if len(kwargs.keys()) > 1:
                            result = (
                                orgs.update_policy(**kwargs)
                                .get("Policy")
                                .get("PolicySummary")
                            )
                            self.write_output(result)
                            return
                        else:
                            self.write_output(policy)
                            return

            result = (
                orgs.create_policy(
                    Name=self.policy_name,
                    Description=self.policy_description,
                    Type="TAG_POLICY",
                    Tags=tags,
                    Content=content,
                )
                .get("Policy")
                .get("PolicySummary")
            )
            self.write_output(result)
