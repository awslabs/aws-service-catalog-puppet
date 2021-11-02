#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from functools import lru_cache

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.generate import generate_policies_template_task


class GeneratePolicies(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    manifest_file_path = luigi.Parameter()
    region = luigi.Parameter()
    sharing_policies = luigi.DictParameter()

    def params_for_results_display(self):
        return {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return {
            "template": generate_policies_template_task.GeneratePoliciesTemplate(
                puppet_account_id=self.puppet_account_id,
                manifest_file_path=self.manifest_file_path,
                region=self.region,
                sharing_policies=self.sharing_policies,
            ),
        }

    def api_calls_used(self):
        return {
            f"cloudformation.create_or_update_{self.puppet_account_id}_{self.region}": 1,
        }

    def run(self):
        template = self.read_from_input("template")
        with self.hub_regional_client("cloudformation") as cloudformation:
            self.info(template)
            cloudformation.create_or_update(
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-policies",
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
            )
        self.write_output(self.get_sharing_policies())

    @lru_cache()
    def get_sharing_policies(self):
        return json.loads(json.dumps(self.sharing_policies.get_wrapped()))
