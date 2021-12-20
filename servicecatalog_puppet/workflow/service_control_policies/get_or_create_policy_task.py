#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from servicecatalog_puppet.workflow import tasks
import luigi


class GetOrCreatePolicyTask(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    region = luigi.Parameter()
    policy_name = luigi.Parameter()
    policy_description = luigi.Parameter()
    policy_content = luigi.DictParameter()
    tags = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "policy_name": self.policy_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"organizations.list_policies_{self.region}",
            f"organizations.create_policy_{self.region}",
        ]

    def run(self):
        with self.hub_regional_client("organizations") as orgs:
            paginator = orgs.get_paginator("list_policies")
            for page in paginator.paginate(Filter="SERVICE_CONTROL_POLICY"):
                for policy in page.get("Policies", []):
                    if policy.get("Name") == self.policy_name:
                        self.write_output(policy)
                        return

            unwrapped = tasks.unwrap(self.policy_content.get("default"))
            content = json.dumps(unwrapped, indent=0, default=str)

            tags = [dict(Key="ServiceCatalogPuppet:Actor", Value="generated")]
            for tag in self.tags:
                tags.append(dict(Key=tag.get("Key"), Value=tag.get("Value")))

            result = (
                orgs.create_policy(
                    Name=self.policy_name,
                    Description=self.policy_description,
                    Type="SERVICE_CONTROL_POLICY",
                    Tags=tags,
                    Content=content,
                )
                .get("Policy")
                .get("PolicySummary")
            )
            self.write_output(result)
