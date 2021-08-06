#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.portfolio.associations import (
    create_associations_for_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.constraints_management import (
    create_launch_role_constraints_for_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    copy_into_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    create_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    delete_portfolio_task,
)
from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
    import_into_spoke_local_portfolio_task,
)
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_base_task,
)


class DoSharePortfolioWithSpokeTask(
    spoke_local_portfolio_base_task.SpokeLocalPortfolioBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    manifest_file_path = luigi.Parameter()
    spoke_local_portfolio_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    sharing_mode = luigi.Parameter()

    product_generation_method = luigi.Parameter()
    organization = luigi.Parameter()
    associations = luigi.ListParameter()
    launch_constraints = luigi.DictParameter()
    portfolio = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        tasks = list()
        organization = self.manifest.get_account(self.account_id).get("organization")
        task_def = self.manifest.get(self.section_name).get(
            self.spoke_local_portfolio_name
        )
        product_generation_method = task_def.get(
            "product_generation_method", constants.PRODUCT_GENERATION_METHOD_DEFAULT
        )
        sharing_mode = task_def.get("sharing_mode", constants.SHARING_MODE_DEFAULT)

        if task_def.get("status") == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED:
            tasks.append(
                delete_portfolio_task.DeletePortfolio(
                    manifest_file_path=self.manifest_file_path,
                    spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                    account_id=self.account_id,
                    region=self.region,
                    portfolio=self.portfolio,
                    product_generation_method=product_generation_method,
                    puppet_account_id=self.puppet_account_id,
                )
            )
        elif task_def.get("status") == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED:

            create_spoke_local_portfolio_task_params = dict(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.account_id,
                region=self.region,
                portfolio=self.portfolio,
                organization=organization,
                sharing_mode=sharing_mode,
            )

            tasks.append(
                create_spoke_local_portfolio_task.CreateSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_params
                )
            )

        create_spoke_local_portfolio_task_as_dependency_params = dict(
            manifest_file_path=self.manifest_file_path,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            organization=organization,
        )

        if len(task_def.get("associations", [])) > 0:
            create_associations_for_portfolio_task = create_associations_for_spoke_local_portfolio_task.CreateAssociationsForSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_as_dependency_params,
                spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                sharing_mode=sharing_mode,
                associations=task_def.get("associations"),
                puppet_account_id=self.puppet_account_id,
            )
            tasks.append(create_associations_for_portfolio_task)

        launch_constraints = task_def.get("constraints", {}).get("launch", [])

        if product_generation_method == "import":
            tasks.append(
                import_into_spoke_local_portfolio_task.ImportIntoSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                    sharing_mode=sharing_mode,
                    puppet_account_id=self.puppet_account_id,
                )
            )
        else:
            tasks.append(
                copy_into_spoke_local_portfolio_task.CopyIntoSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                    sharing_mode=sharing_mode,
                    puppet_account_id=self.puppet_account_id,
                )
            )

        if len(launch_constraints) > 0:
            create_launch_role_constraints_for_portfolio_task_params = dict(
                launch_constraints=launch_constraints,
                puppet_account_id=self.puppet_account_id,
            )
            create_launch_role_constraints_for_portfolio = create_launch_role_constraints_for_spoke_local_portfolio_task.CreateLaunchRoleConstraintsForSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_as_dependency_params,
                **create_launch_role_constraints_for_portfolio_task_params,
                spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                sharing_mode=sharing_mode,
                product_generation_method=product_generation_method,
            )
            tasks.append(create_launch_role_constraints_for_portfolio)
        return tasks

    def run(self):
        self.write_output(self.params_for_results_display())
