#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import re

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import utils
from servicecatalog_puppet.workflow.general import delete_cloud_formation_stack_task
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    copy_into_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    import_into_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    portfolio_management_task,
)
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)


class CreateUpdateResourceConstraintsForSpokeLocalPortfolioTask(
    portfolio_management_task.PortfolioManagementTask
):
    portfolio_task_reference = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    resource_update_constraints = luigi.DictParameter()

    manifest_task_reference_file_path = luigi.Parameter()
    task_reference = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "portfolio": self.portfolio,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(
            reference_dependencies=get_dependencies_for_task_reference(
                self.manifest_task_reference_file_path,
                self.task_reference,
                self.puppet_account_id,
            )
        )

    def api_calls_used(self):
        return [
            f"cloudformation.ensure_deleted_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
            f"cloudformation.create_or_update_{self.account_id}_{self.region}",
            f"service_catalog.search_products_as_admin_{self.account_id}_{self.region}",
        ]

    def run(self):
        # dependency_output = self.load_from_input("create_spoke_local_portfolio_task")
        # spoke_portfolio = dependency_output.get("portfolio")
        # portfolio_id = spoke_portfolio.get("Id")

        raise Exception(
            self.input()
            .get("reference_dependencies")
            .get(self.portfolio_task_reference)
            .open("r")
            .read()
        )

        product_name_to_id_dict = dependency_output.get("products")
        with self.spoke_regional_client("cloudformation") as cloudformation:
            new_constraints = self.generate_new_constraints(
                portfolio_id, product_name_to_id_dict
            )

            template = config.env.get_template(
                "update_resource_constraints.template.yaml.j2"
            ).render(
                portfolio={"DisplayName": self.portfolio,},
                portfolio_id=portfolio_id,
                update_resource_constraints=new_constraints,
                product_name_to_id_dict=product_name_to_id_dict,
            )
            stack_name = f"update-resource-constraints-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}"
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

    def generate_new_constraints(self, portfolio_id, product_name_to_id_dict):
        new_constraints = []
        for constraint in self.resource_update_constraints:
            new_constraint = {
                "products": [],
                "tag_update_on_provisioned_product": constraint.get(
                    "tag_update_on_provisioned_product"
                ),
            }
            if constraint.get("products", None) is not None:
                if isinstance(constraint.get("products"), tuple):
                    new_constraint["products"] += constraint.get("products")
                elif isinstance(constraint.get("products"), str):
                    with self.spoke_regional_client(
                        "servicecatalog"
                    ) as service_catalog:
                        response = service_catalog.search_products_as_admin_single_page(
                            PortfolioId=portfolio_id
                        )
                        for product_view_details in response.get(
                            "ProductViewDetails", []
                        ):
                            product_view_summary = product_view_details.get(
                                "ProductViewSummary"
                            )
                            product_name_to_id_dict[
                                product_view_summary.get("Name")
                            ] = product_view_summary.get("ProductId")
                            if re.match(
                                constraint.get("products"),
                                product_view_summary.get("Name"),
                            ):
                                new_constraint["products"].append(
                                    product_view_summary.get("Name")
                                )
                else:
                    raise Exception(
                        f'Unexpected launch constraint type {type(constraint.get("products"))}'
                    )

            if constraint.get("product", None) is not None:
                new_constraint["products"].append(constraint.get("product"))

            new_constraints.append(new_constraint)
        return new_constraints
