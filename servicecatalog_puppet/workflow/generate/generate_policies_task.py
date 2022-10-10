#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from servicecatalog_puppet import serialisation_utils
from functools import lru_cache

import luigi

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow.dependencies import tasks


class GeneratePolicies(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    organizations_to_share_with = luigi.ListParameter()
    ous_to_share_with = luigi.ListParameter()
    accounts_to_share_with = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        sharing_policies = dict(
            accounts=self.accounts_to_share_with,
            ous=self.ous_to_share_with,
            organizations=self.organizations_to_share_with,
        )

        if len(sharing_policies.get("accounts", [])) > 50:
            self.warning(
                "You have specified more than 50 accounts will not create the eventbus policy and spoke execution mode will not work"
            )
        template = config.env.get_template("policies.template.yaml.j2").render(
            sharing_policies=sharing_policies,
            VERSION=constants.VERSION,
            HOME_REGION=constants.HOME_REGION,
        )

        with self.spoke_regional_client("cloudformation") as cloudformation:
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
                Tags=self.initialiser_stack_tags,
            )
        self.write_empty_output()
