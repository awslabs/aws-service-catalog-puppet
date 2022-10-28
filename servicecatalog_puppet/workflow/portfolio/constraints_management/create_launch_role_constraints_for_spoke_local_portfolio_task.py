#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import re

import luigi
import troposphere as t
from troposphere import servicecatalog

from servicecatalog_puppet import config
from servicecatalog_puppet import utils
from servicecatalog_puppet.workflow.dependencies import tasks


class CreateLaunchRoleConstraintsForSpokeLocalPortfolioTask(tasks.TaskWithReference):
    portfolio_task_reference = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    launch_constraints = luigi.ListParameter()

    portfolio_get_all_products_and_their_versions_ref = luigi.Parameter()

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
        products_and_their_versions = self.get_output_from_reference_dependency(
            self.portfolio_get_all_products_and_their_versions_ref
        )

        tpl = t.Template()
        tpl.description = f"launch constraints for {self.portfolio}"

        for launch_constraint in self.launch_constraints:
            products_to_constrain = list()
            constraint = launch_constraint.get("products") or launch_constraint.get(
                "product"
            )
            if isinstance(constraint, tuple):
                for p in constraint:
                    products_to_constrain.append(p)
            elif isinstance(constraint, str):
                products_to_constrain.append(constraint)
            else:
                raise Exception(
                    f"Unexpected launch constraint type in {type(constraint)}"
                )

            for role_arn in launch_constraint.get("roles"):
                for product_to_constrain in products_to_constrain:
                    for (
                        product_name,
                        product_details,
                    ) in products_and_their_versions.items():
                        if re.match(product_to_constrain, product_name,):
                            product_id = product_details.get("ProductId")
                            tpl.add_resource(
                                servicecatalog.LaunchRoleConstraint(
                                    f"L{portfolio_id}B{product_id}C{role_arn.split(':')[-1]}".replace(
                                        "-", ""
                                    ).replace(
                                        "/", ""
                                    ),
                                    PortfolioId=portfolio_id,
                                    ProductId=product_id,
                                    RoleArn=role_arn.replace(
                                        "${AWS::AccountId}", self.account_id
                                    ),
                                )
                            )

        template_to_use = tpl.to_yaml()

        with self.spoke_regional_client("cloudformation") as cloudformation:
            stack_name = f"launch-constraints-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}"
            cloudformation.create_or_update(
                StackName=stack_name,
                TemplateBody=template_to_use,
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
            self.write_empty_output()
