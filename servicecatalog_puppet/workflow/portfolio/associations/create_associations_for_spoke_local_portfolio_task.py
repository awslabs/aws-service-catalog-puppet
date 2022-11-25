#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import re

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import utils
from servicecatalog_puppet.workflow.dependencies import tasks
import troposphere as t
from troposphere import s3, servicecatalog


class CreateAssociationsForSpokeLocalPortfolioTask(tasks.TaskWithReference):
    portfolio_task_reference = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()

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

    def run(self):
        portfolio_details = self.get_output_from_reference_dependency(
            self.portfolio_task_reference
        )
        portfolio_id = portfolio_details.get("Id")

        haystack = "".join(self.associations)
        used_wildcard = "*" in haystack
        used_roles = ":role/" in haystack
        used_users = ":user/" in haystack
        used_groups = ":group/" in haystack

        if used_wildcard:
            roles = list()
            users = list()
            groups = list()
            with self.spoke_regional_client("iam") as iam:
                if used_roles:
                    paginator = iam.get_paginator("list_roles")
                    for page in paginator.paginate():
                        roles += page.get("Roles", [])
                if used_users:
                    paginator = iam.get_paginator("list_users")
                    for page in paginator.paginate():
                        users += page.get("Users", [])
                if used_groups:
                    paginator = iam.get_paginator("list_groups")
                    for page in paginator.paginate():
                        groups += page.get("Groups", [])

            associations_to_use = list()
            for association in self.associations:
                if "*" in association:
                    association_as_a_regex = re.escape(
                        association.replace("${AWS::AccountId}", self.account_id)
                    ).replace("\\*", "(.*)")
                    if ":role/" in association:
                        for role_object in roles:
                            role = role_object.get("Arn")
                            if re.match(association_as_a_regex, role):
                                associations_to_use.append(role)
                    if ":user/" in association:
                        for user_object in users:
                            user = user_object.get("Arn")
                            if re.match(association_as_a_regex, user):
                                associations_to_use.append(user)
                    if ":group/" in association:
                        for group_object in groups:
                            group = group_object.get("Arn")
                            if re.match(association_as_a_regex, group):
                                associations_to_use.append(group)
                else:
                    associations_to_use.append(association)
        else:
            associations_to_use = self.associations

        with self.spoke_regional_client("cloudformation") as cloudformation:
            v1_stack_name = f"associations-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}"
            cloudformation.ensure_deleted(StackName=v1_stack_name)

            v2_stack_name = f"associations-v2-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}"
            if associations_to_use:
                tpl = t.Template()
                tpl.description = f"Associations for {self.portfolio}"
                for association_to_use in associations_to_use:
                    logical_name = "".join(
                        filter(
                            str.isalnum,
                            f"{portfolio_id}{association_to_use.split(':')[-1]}",
                        )
                    )
                    tpl.add_resource(
                        servicecatalog.PortfolioPrincipalAssociation(
                            logical_name,
                            PortfolioId=portfolio_id,
                            PrincipalARN=t.Sub(association_to_use),
                            PrincipalType="IAM",
                        )
                    )
                template = tpl.to_yaml()
                cloudformation.create_or_update(
                    StackName=v2_stack_name,
                    TemplateBody=template,
                    NotificationARNs=[
                        f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                    ]
                    if self.should_use_sns
                    else [],
                    ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                    Tags=self.initialiser_stack_tags,
                )
            else:
                cloudformation.ensure_deleted(StackName=v2_stack_name)
        self.write_empty_output()
