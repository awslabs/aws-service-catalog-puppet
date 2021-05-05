import luigi

from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import (
    dependency,
    portfoliomanagement as portfoliomanagement_tasks,
)


class SpokeLocalPortfolioBaseTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def status(self):
        return (
            self.manifest.get(self.section_name)
            .get(self.spoke_local_portfolio_name)
            .get("status", constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED)
        )

    @property
    def section_name(self):
        return constants.SPOKE_LOCAL_PORTFOLIOS


class SpokeLocalPortfolioSectionTask(manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    def should_run(self):
        return (
            self.execution_mode == constants.EXECUTION_MODE_HUB and not self.is_dry_run
        )

    def requires(self):
        requirements = dict()
        if self.should_run():
            requirements["spoke_local_portfolio_tasks"] = [
                SpokeLocalPortfolioTask(
                    spoke_local_portfolio_name=spoke_local_portfolio_name,
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                )
                for spoke_local_portfolio_name, spoke_local_portfolio in self.manifest.get(
                    "spoke-local-portfolios", {}
                ).items()
            ]

        return requirements

    def run(self):
        self.write_output(self.manifest.get("spoke-local-portfolios"))


class SpokeLocalPortfolioForTask(
    SpokeLocalPortfolioBaseTask, manifest_tasks.ManifestMixen
):
    spoke_local_portfolio_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        raise NotImplementedError()

    def get_klass_for_provisioning(self):
        if self.status == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED:
            return SharePortfolioWithSpokeTask
        elif self.status == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED:
            return TerminatePortfolioInSpokeTask
        else:
            raise Exception(f"Unknown status: {self.status}")

    def run(self):
        self.write_output(self.params_for_results_display())


class SpokeLocalPortfolioForRegionTask(SpokeLocalPortfolioForTask):
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        these_dependencies = list()
        requirements = dict(
            dependencies=dependencies, these_dependencies=these_dependencies,
        )

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
            self.puppet_account_id,
            self.section_name,
            self.spoke_local_portfolio_name,
            self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        spoke_portfolio = self.manifest.get(self.section_name).get(
            self.spoke_local_portfolio_name
        )
        for depends_on in spoke_portfolio.get("depends_on", []):
            if depends_on.get("type") == constants.SPOKE_LOCAL_PORTFOLIO:
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        self.__class__(
                            manifest_file_path=self.manifest_file_path,
                            launch_name=depends_on.get("name"),
                            puppet_account_id=self.puppet_account_id,
                            region=self.region,
                        )
                    )

        return requirements


class SpokeLocalPortfolioForAccountTask(SpokeLocalPortfolioForTask):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
            self.puppet_account_id,
            self.section_name,
            self.spoke_local_portfolio_name,
            self.account_id,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class SpokeLocalPortfolioForAccountAndRegionTask(SpokeLocalPortfolioForTask):
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_account_and_region(
            self.puppet_account_id,
            self.section_name,
            self.spoke_local_portfolio_name,
            self.account_id,
            self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class SpokeLocalPortfolioTask(SpokeLocalPortfolioForTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        regional_dependencies = list()
        account_dependencies = list()
        account_and_region_dependencies = list()
        requirements = dict(
            regional_launches=regional_dependencies,
            account_launches=account_dependencies,
            account_and_region_dependencies=account_and_region_dependencies,
        )

        for region in self.manifest.get_regions_used_for_section_item(
            self.puppet_account_id, self.section_name, self.spoke_local_portfolio_name
        ):
            regional_dependencies.append(
                SpokeLocalPortfolioForRegionTask(**self.param_kwargs, region=region,)
            )

        for account_id in self.manifest.get_account_ids_used_for_section_item(
            self.puppet_account_id, self.section_name, self.spoke_local_portfolio_name
        ):
            account_dependencies.append(
                SpokeLocalPortfolioForAccountTask(
                    **self.param_kwargs, account_id=account_id,
                )
            )

        for (
            account_id,
            regions,
        ) in self.manifest.get_account_ids_and_regions_used_for_section_item(
            self.puppet_account_id, self.section_name, self.spoke_local_portfolio_name
        ).items():
            for region in regions:
                account_and_region_dependencies.append(
                    SpokeLocalPortfolioForAccountAndRegionTask(
                        **self.param_kwargs, account_id=account_id, region=region,
                    )
                )

        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


class DoTerminatePortfolioInSpokeTask(
    SpokeLocalPortfolioBaseTask,
    manifest_tasks.ManifestMixen,
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
        return portfoliomanagement_tasks.DeletePortfolio(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            product_generation_method=self.product_generation_method,
            puppet_account_id=self.puppet_account_id,
        )

    def run(self):
        self.write_output(self.params_for_results_display())


class TerminatePortfolioInSpokeTask(
    SpokeLocalPortfolioBaseTask,
    manifest_tasks.ManifestMixen,
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
        return dict(section_dependencies=self.get_section_dependencies())

    def run(self):
        yield DoTerminatePortfolioInSpokeTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            puppet_account_id=self.puppet_account_id,
            sharing_mode=self.sharing_mode,
            product_generation_method=self.product_generation_method,
            organization=self.organization,
            associations=self.associations,
            launch_constraints=self.launch_constraints,
            portfolio=self.portfolio,
            region=self.region,
            account_id=self.account_id,
        )
        self.write_output(self.params_for_results_display())


class SharePortfolioWithSpokeTask(
    SpokeLocalPortfolioBaseTask,
    manifest_tasks.ManifestMixen,
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
        return dict(section_dependencies=self.get_section_dependencies())

    def run(self):
        yield DoSharePortfolioWithSpokeTask(
            manifest_file_path=self.manifest_file_path,
            spoke_local_portfolio_name=self.spoke_local_portfolio_name,
            puppet_account_id=self.puppet_account_id,
            sharing_mode=self.sharing_mode,
            product_generation_method=self.product_generation_method,
            organization=self.organization,
            associations=self.associations,
            launch_constraints=self.launch_constraints,
            portfolio=self.portfolio,
            region=self.region,
            account_id=self.account_id,
        )
        self.write_output(self.params_for_results_display())


class DoSharePortfolioWithSpokeTask(
    SpokeLocalPortfolioBaseTask,
    manifest_tasks.ManifestMixen,
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
                portfoliomanagement_tasks.DeletePortfolio(
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

            create_spoke_local_portfolio_task = portfoliomanagement_tasks.CreateSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_params
            )
            tasks.append(create_spoke_local_portfolio_task)

        create_spoke_local_portfolio_task_as_dependency_params = dict(
            manifest_file_path=self.manifest_file_path,
            account_id=self.account_id,
            region=self.region,
            portfolio=self.portfolio,
            organization=organization,
        )

        if len(task_def.get("associations", [])) > 0:
            create_associations_for_portfolio_task = portfoliomanagement_tasks.CreateAssociationsForSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_as_dependency_params,
                spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                sharing_mode=sharing_mode,
                associations=task_def.get("associations"),
                puppet_account_id=self.puppet_account_id,
            )
            tasks.append(create_associations_for_portfolio_task)

        launch_constraints = task_def.get("constraints", {}).get("launch", [])

        if product_generation_method == "import":
            import_into_spoke_local_portfolio_task = portfoliomanagement_tasks.ImportIntoSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_as_dependency_params,
                spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                sharing_mode=sharing_mode,
                puppet_account_id=self.puppet_account_id,
            )
            tasks.append(import_into_spoke_local_portfolio_task)
        else:
            copy_into_spoke_local_portfolio_task = portfoliomanagement_tasks.CopyIntoSpokeLocalPortfolioTask(
                **create_spoke_local_portfolio_task_as_dependency_params,
                spoke_local_portfolio_name=self.spoke_local_portfolio_name,
                sharing_mode=sharing_mode,
                puppet_account_id=self.puppet_account_id,
            )
            tasks.append(copy_into_spoke_local_portfolio_task)

        if len(launch_constraints) > 0:
            create_launch_role_constraints_for_portfolio_task_params = dict(
                launch_constraints=launch_constraints,
                puppet_account_id=self.puppet_account_id,
            )
            create_launch_role_constraints_for_portfolio = portfoliomanagement_tasks.CreateLaunchRoleConstraintsForSpokeLocalPortfolioTask(
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
