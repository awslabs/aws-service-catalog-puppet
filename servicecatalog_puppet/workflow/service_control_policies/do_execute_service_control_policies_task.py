#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.service_control_policies import (
    service_control_policies_base_task,
    get_or_create_policy_task,
)
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from betterboto import client as betterboto_client


class DoExecuteServiceControlPoliciesTask(
    service_control_policies_base_task.ServiceControlPoliciesBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    service_control_policy_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    content = luigi.DictParameter()
    should_minimize = luigi.BoolParameter()
    description = luigi.Parameter()

    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "service_control_policy_name": self.service_control_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(policy=get_or_create_policy_task.GetOrCreatePolicyTask(
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            policy_name=self.service_control_policy_name,
            policy_description=self.description,
            policy_content=self.content,
            should_minimize=self.should_minimize,
            tags=self.manifest.get(constants.SERVICE_CONTROL_POLICIES).get(self.service_control_policy_name).get("tags", [])
        ))

    def api_calls_used(self):
        return [
            f"organizations.attach_policy_{self.region}",
        ]

    def has_policy_attached(self, orgs):
        paginator = orgs.get_paginator("list_policies_for_target")
        for page in paginator.paginate(TargetId=self.account_id, Filter="SERVICE_CONTROL_POLICY"):
            for policy in page.get("Policies", []):
                if policy.get("Name") == self.service_control_policy_name:
                    return True
        return False

    def run(self):
        with self.hub_regional_client("organizations") as orgs:
            self.info("Ensuring attachments for policies")
            policy_id = self.load_from_input("policy").get("Id")
            if self.has_policy_attached(orgs):
                self.write_output("Skipped")
            else:
                orgs.attach_policy(PolicyId=policy_id, TargetId=self.account_id)
                self.write_output(self.params_for_results_display())

            # for policy, policy_details in section.get("policies", {}).items():
            #     policy_id = already_created_policies[policy]
            #     for raw_target in policy_details.get("targets", []):
            #         if re.match(r"[0-9]{12}", str(raw_target)):
            #             target = raw_target
            #         elif str(raw_target).startswith("/"):
            #             # target is an ou path
            #             target = orgs.convert_path_to_ou(raw_target)
            #         else:
            #             target = raw_target
        #
        #     self.info("Ensuring attachments")
        #     for attachment in section.get("attachments", []):
        #         policy_id = already_created_policies[attachment.get("policy")]
        #         for raw_target in attachment.get("targets", []):
        #             if re.match(r"[0-9]{12}", str(raw_target)):
        #                 target = raw_target
        #             elif str(raw_target).startswith("/"):
        #                 # target is an ou path
        #                 target = orgs.convert_path_to_ou(raw_target)
        #             else:
        #                 target = raw_target
        #             orgs.attach_policy(PolicyId=policy_id, TargetId=target)
        #     self.info("Ensuring attachments complete")
        # self.write_output(self.params_for_results_display())
