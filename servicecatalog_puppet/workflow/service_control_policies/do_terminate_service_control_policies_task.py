#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import functools

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet import serialisation_utils
from servicecatalog_puppet.workflow.dependencies import tasks
from servicecatalog_puppet.workflow.service_control_policies import (
    get_or_create_policy_task,
)


class DoTerminateServiceControlPoliciesTask(tasks.TaskWithReference):
    service_control_policy_name = luigi.Parameter()

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
            "service_control_policy_name": self.service_control_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "ou_name": self.ou_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        manifest = serialisation_utils.load(open(self.manifest_file_path, "r").read())
        return dict(
            reference_dependencies=self.dependencies_for_task_reference(),
            policy=get_or_create_policy_task.GetOrCreatePolicyTask(
                puppet_account_id=self.puppet_account_id,
                region=self.region,
                policy_name=self.service_control_policy_name,
                policy_description=self.description,
                policy_content=self.content,
                tags=manifest.get(constants.SERVICE_CONTROL_POLICIES)
                .get(self.service_control_policy_name)
                .get("tags", []),
            ),
        )

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
        for page in paginator.paginate(
            TargetId=self.target(), Filter="SERVICE_CONTROL_POLICY"
        ):
            for policy in page.get("Policies", []):
                if policy.get("Name") == self.service_control_policy_name:
                    return True
        return False

    def run(self):
        with self.organizations_policy_client() as orgs:
            self.info("Ensuring attachments for policies")
            policy_id = self.load_from_input("policy").get("Id")
            if self.has_policy_attached(orgs):
                orgs.detach_policy(PolicyId=policy_id, TargetId=self.target())
                self.write_empty_output()
            else:
                self.write_empty_output()
