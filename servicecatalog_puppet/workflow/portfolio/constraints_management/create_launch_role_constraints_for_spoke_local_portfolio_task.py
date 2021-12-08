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


class CreateLaunchRoleConstraintsForSpokeLocalPortfolioTask(
    portfolio_management_task.PortfolioManagementTask
):
    spoke_local_portfolio_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    portfolio = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    organization = luigi.Parameter()
    product_generation_method = luigi.Parameter()
    launch_constraints = luigi.DictParameter()

    sharing_mode = luigi.Parameter()

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
        create_spoke_local_portfolio_task_klass = (
            import_into_spoke_local_portfolio_task.ImportIntoSpokeLocalPortfolioTask
            if self.product_generation_method == "import"
            else copy_into_spoke_local_portfolio_task.CopyIntoSpokeLocalPortfolioTask
        )

        return dict(
            create_spoke_local_portfolio_task=create_spoke_local_portfolio_task_klass(
                spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                manifest_file_path=self.manifest_file_path,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                organization=self.organization,
                puppet_account_id=self.puppet_account_id,
                sharing_mode=self.sharing_mode,
            ),
        )

    def api_calls_used(self):
        return [
            f"cloudformation.ensure_deleted_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
            f"cloudformation.create_or_update_{self.account_id}_{self.region}",
            f"service_catalog.search_products_as_admin_{self.account_id}_{self.region}",
        ]

    def run(self):
        dependency_output = self.load_from_input("create_spoke_local_portfolio_task")
        spoke_portfolio = dependency_output.get("portfolio")
        portfolio_id = spoke_portfolio.get("Id")

        yield [
            delete_cloud_formation_stack_task.DeleteCloudFormationStackTask(
                account_id=self.account_id,
                region=self.region,
                stack_name=f"launch-constraints-for-portfolio-{portfolio_id}",
                nonce="forever",
            ),
            delete_cloud_formation_stack_task.DeleteCloudFormationStackTask(
                account_id=self.account_id,
                region=self.region,
                stack_name=f"launch-constraints-v2-for-portfolio-{portfolio_id}",
                nonce="forever",
            ),
        ]

        product_name_to_id_dict = dependency_output.get("products")
        with self.spoke_regional_client("cloudformation") as cloudformation:
            new_launch_constraints = self.generate_new_launch_constraints(
                portfolio_id, product_name_to_id_dict
            )

            template = config.env.get_template(
                "launch_role_constraints.template.yaml.j2"
            ).render(
                portfolio={"DisplayName": self.portfolio,},
                portfolio_id=portfolio_id,
                launch_constraints=new_launch_constraints,
                product_name_to_id_dict=product_name_to_id_dict,
            )
            stack_name = f"launch-constraints-for-{utils.slugify_for_cloudformation_stack_name(self.spoke_local_portfolio_name)}"
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

    def generate_new_launch_constraints(self, portfolio_id, product_name_to_id_dict):
        new_launch_constraints = []
        for launch_constraint in self.launch_constraints:
            new_launch_constraint = {
                "products": [],
                "roles": launch_constraint.get("roles"),
            }
            if launch_constraint.get("products", None) is not None:
                if isinstance(launch_constraint.get("products"), tuple):
                    new_launch_constraint["products"] += launch_constraint.get(
                        "products"
                    )
                elif isinstance(launch_constraint.get("products"), str):
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
                                launch_constraint.get("products"),
                                product_view_summary.get("Name"),
                            ):
                                new_launch_constraint["products"].append(
                                    product_view_summary.get("Name")
                                )
                else:
                    raise Exception(
                        f'Unexpected launch constraint type {type(launch_constraint.get("products"))}'
                    )

            if launch_constraint.get("product", None) is not None:
                new_launch_constraint["products"].append(
                    launch_constraint.get("product")
                )

            new_launch_constraints.append(new_launch_constraint)
        return new_launch_constraints
