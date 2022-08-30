#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import re

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import utils
from servicecatalog_puppet.workflow.dependencies import tasks
from servicecatalog_puppet.workflow.general import delete_cloud_formation_stack_task


class CreateAssociationsForSpokeLocalPortfolioTask(tasks.TaskWithReference):
    portfolio_task_reference = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    associations = luigi.ListParameter(default=[])

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        calls = [
            f"cloudformation.create_or_update_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
        ]
        used_wildcard = "*" in "".join(self.associations)
        if used_wildcard:
            calls.append(f"iam.list_roles_{self.account_id}_{self.region}")
        return calls

    def run(self):
        portfolio_details = json.loads(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_task_reference)
            .open("r")
            .read()
        )
        portfolio_id = portfolio_details.get("Id")

        yield delete_cloud_formation_stack_task.DeleteCloudFormationStackTask(
            account_id=self.account_id,
            region=self.region,
            stack_name=f"associations-for-portfolio-{portfolio_id}",
            nonce="forever",
        )

        used_wildcard = "*" in "".join(self.associations)

        if used_wildcard:
            roles = list()
            with self.spoke_regional_client("iam") as iam:
                paginator = iam.get_paginator("list_roles")
                for page in paginator.paginate():
                    roles += page.get("Roles", [])

            associations_to_use = list()
            for association in self.associations:
                if "*" in association:
                    association_as_a_regex = re.escape(
                        association.replace("${AWS::AccountId}", self.account_id)
                    ).replace("\\*", "(.*)")
                    for role_object in roles:
                        role = role_object.get("Arn")
                        if re.match(association_as_a_regex, role):
                            associations_to_use.append(role)
                else:
                    associations_to_use.append(association)
        else:
            associations_to_use = self.associations

        with self.spoke_regional_client("cloudformation") as cloudformation:
            template = config.env.get_template("associations.template.yaml.j2").render(
                portfolio={
                    "DisplayName": self.portfolio,
                    "Associations": associations_to_use,
                },
                portfolio_id=portfolio_id,
            )
            stack_name = f"associations-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}"
            cloudformation.create_or_update(
                StackName=stack_name,
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )
            result = cloudformation.describe_stacks(StackName=stack_name,).get(
                "Stacks"
            )[0]
            self.write_output(result)
