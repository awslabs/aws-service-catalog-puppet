#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import functools

import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class DoExecuteTagPoliciesTask(tasks.TaskWithReference):
    tag_policy_name = luigi.Parameter()

    get_or_create_policy_ref = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()
    ou_name = luigi.Parameter()

    content = luigi.DictParameter()
    description = luigi.Parameter()

    requested_priority = luigi.IntParameter()
    manifest_file_path = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "tag_policy_name": self.tag_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "ou_name": self.ou_name,
            "cache_invalidator": self.cache_invalidator,
        }

    @functools.lru_cache(maxsize=32)
    def target(self):
        with self.organizations_policy_client() as orgs:
            if self.account_id != "":
                return self.account_id
            else:
                if str(self.ou_name).startswith("/"):
                    return orgs.convert_path_to_ou(self.ou_name)
                else:
                    return self.ou_name

    def has_policy_attached(self, orgs):
        paginator = orgs.get_paginator("list_policies_for_target")
        for page in paginator.paginate(TargetId=self.target(), Filter="TAG_POLICY"):
            for policy in page.get("Policies", []):
                if policy.get("Name") == self.tag_policy_name:
                    return True
        return False

    def run(self):
        with self.organizations_policy_client() as orgs:
            self.info("Ensuring attachments for policies")
            policy_id = self.get_output_from_reference_dependency(
                self.get_or_create_policy_ref
            ).get("Id")
            if self.has_policy_attached(orgs):
                self.write_empty_output()
            else:
                orgs.attach_policy(PolicyId=policy_id, TargetId=self.target())
                self.write_empty_output()
