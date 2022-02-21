#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from betterboto import client as betterboto_client
import luigi
import re


class ServiceControlPolicySectionTask(tasks.PuppetTask, manifest_mixin.ManifestMixen):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        section = self.manifest.get(constants.SERVICE_CONTROL_POLICIES, {})
        already_created_policies = dict()
        with self.organizations_policy_client() as orgs:
            self.info("Ensuring policies are created")
            paginator = orgs.get_paginator("list_policies")
            for page in paginator.paginate(Filter="SERVICE_CONTROL_POLICIES"):
                for policy in page.get("Policies", []):
                    if already_created_policies.get(policy.get("Name")):
                        raise Exception(
                            f"Policy {policy.get('Name')} exists more than once"
                        )
                    already_created_policies[policy.get("Name")] = policy.get("Id")

            for policy_name, policy in section.get("policies", {}).items():
                if already_created_policies.get(policy_name) is None:
                    description = policy.get("description", policy_name)
                    tags = policy.get("tags", [])
                    content = json.dumps(json.loads(policy.get("content")))
                    policy_id = (
                        orgs.create_policy(
                            Name=policy_name,
                            Description=description,
                            Type="SERVICE_CONTROL_POLICY",
                            Tags=tags,
                            Content=content,
                        )
                        .get("Policy")
                        .get("PolicySummary")
                        .get("Id")
                    )
                    already_created_policies[policy_name] = policy_id
            self.info("Ensuring policies are created completed")

            self.info("Ensuring attachments for policies")
            for policy, policy_details in section.get("policies", {}).items():
                policy_id = already_created_policies[policy]
                for raw_target in policy_details.get("targets", []):
                    if re.match(r"[0-9]{12}", str(raw_target)):
                        target = raw_target
                    elif str(raw_target).startswith("/"):
                        # target is an ou path
                        target = orgs.convert_path_to_ou(raw_target)
                    else:
                        target = raw_target
                    orgs.attach_policy(PolicyId=policy_id, TargetId=target)
            self.info("Ensuring attachments for policies complete")

            self.info("Ensuring attachments")
            for attachment in section.get("attachments", []):
                policy_id = already_created_policies[attachment.get("policy")]
                for raw_target in attachment.get("targets", []):
                    if re.match(r"[0-9]{12}", str(raw_target)):
                        target = raw_target
                    elif str(raw_target).startswith("/"):
                        # target is an ou path
                        target = orgs.convert_path_to_ou(raw_target)
                    else:
                        target = raw_target
                    orgs.attach_policy(PolicyId=policy_id, TargetId=target)
            self.info("Ensuring attachments complete")
        self.write_output(self.params_for_results_display())
