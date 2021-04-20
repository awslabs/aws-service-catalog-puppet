
import luigi

from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet import constants, config
from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import launch as launch_tasks


class SpokeLocalPortfolioBaseTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def status(self):
        return self.manifest.get(self.section_name).get(self.spoke_local_portfolio_name).get("status", constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED)

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
        return self.execution_mode == constants.EXECUTION_MODE_HUB and not self.is_dry_run

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


class SpokeLocalPortfolioForTask(SpokeLocalPortfolioBaseTask, manifest_tasks.ManifestMixen):
    spoke_local_portfolio_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def get_klass_for_provisioning(self):
        if self.status == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED:
            return SharePortfolioWithSpokeTask
        # elif self.status == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED:
        #     return TerminatePortfolioInSpokeTask
        else:
            raise Exception(f"Unknown status: {self.status}")

    def run(self):
        self.write_output(self.params_for_results_display())


class SpokeLocalPortfolioForRegionTask(SpokeLocalPortfolioForTask):
    region = luigi.Parameter()

    def requires(self):
        dependencies = list()
        these_dependencies = list()
        requirements = dict(
            dependencies=dependencies, these_dependencies=these_dependencies,
        )

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
                self.puppet_account_id, self.section_name, self.spoke_local_portfolio_name, self.region
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        spoke_portfolio = self.manifest.get(self.section_name).get(self.spoke_local_portfolio_name)
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

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
                self.puppet_account_id, self.section_name, self.spoke_local_portfolio_name, self.account_id
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class SpokeLocalPortfolioForAccountAndRegionTask(SpokeLocalPortfolioForTask):
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies)

        klass = self.get_klass_for_provisioning()

        for (
                task
        ) in self.manifest.get_tasks_for_launch_and_account_and_region(
            self.puppet_account_id, self.section_name, self.spoke_local_portfolio_name, self.account_id, self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class SpokeLocalPortfolioTask(SpokeLocalPortfolioForTask):

    def params_for_results_display(self):
        return {
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
                SpokeLocalPortfolioForRegionTask(**self.param_kwargs, region=region, )
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
                        **self.param_kwargs,
                        account_id=account_id,
                        region=region,
                    )
                )

        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


class SharePortfolioWithSpokeTask(SpokeLocalPortfolioBaseTask, manifest_tasks.ManifestMixen):
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
        these_dependencies = list()
        dependencies = dict(
            these_dependencies=these_dependencies
        )
        this_item = self.manifest.get(self.section_name).get(self.spoke_local_portfolio_name)
        for depends_on in this_item.get("depends_on", []):
            if depends_on.get("type") == constants.LAUNCH:
                if depends_on.get(constants.AFFINITY) == "launch":
                    these_dependencies.append(
                        launch_tasks.LaunchTask(
                            manifest_file_path=self.manifest_file_path,
                            launch_name=depends_on.get("name"),
                            puppet_account_id=self.puppet_account_id,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account":
                    these_dependencies.append(
                        launch_tasks.LaunchForAccountTask(
                            manifest_file_path=self.manifest_file_path,
                            launch_name=depends_on.get("name"),
                            puppet_account_id=self.puppet_account_id,
                            account_id=self.account_id,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        launch_tasks.LaunchForRegionTask(
                            manifest_file_path=self.manifest_file_path,
                            launch_name=depends_on.get("name"),
                            puppet_account_id=self.puppet_account_id,
                            region=self.region,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account-and-region":
                    these_dependencies.append(
                        launch_tasks.LaunchForAccountAndRegionTask(
                            manifest_file_path=self.manifest_file_path,
                            launch_name=depends_on.get("name"),
                            puppet_account_id=self.puppet_account_id,
                            account_id=self.account_id,
                            region=self.region,
                        )
                    )
        return dependencies

    def run(self):
        self.write_output(self.params_for_results_display())

    #         self.info("generate_tasks main loop iteration 1")
    #         product_generation_method = task_def.get(
    #             "product_generation_method", "copy"
    #         )
    #
    #         sharing_mode = task_def.get("sharing_mode", constants.SHARING_MODE_DEFAULT)
    #
    #         self.info("generate_tasks main loop iteration 2")
    #         if (
    #             task_def.get("status")
    #             == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED
    #         ):
    #             tasks.append(
    #                 portfoliomanagement_tasks.DeletePortfolio(
    #                     manifest_file_path=self.manifest_file_path,
    #                     spoke_local_portfolio_name=self.spoke_local_portfolio_name,
    #                     account_id=task_def.get("account_id"),
    #                     region=task_def.get("region"),
    #                     portfolio=task_def.get("portfolio"),
    #                     product_generation_method=product_generation_method,
    #                     puppet_account_id=task_def.get("puppet_account_id"),
    #                 )
    #             )
    #         elif (
    #             task_def.get("status") == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED
    #         ):
    #
    #             create_spoke_local_portfolio_task_params = dict(
    #                 manifest_file_path=self.manifest_file_path,
    #                 puppet_account_id=self.puppet_account_id,
    #                 account_id=task_def.get("account_id"),
    #                 region=task_def.get("region"),
    #                 portfolio=task_def.get("portfolio"),
    #                 organization=task_def.get("organization"),
    #                 sharing_mode=sharing_mode,
    #             )
    #
    #             create_spoke_local_portfolio_task = portfoliomanagement_tasks.CreateSpokeLocalPortfolioTask(
    #                 **create_spoke_local_portfolio_task_params
    #             )
    #             tasks.append(create_spoke_local_portfolio_task)
    #
    #         create_spoke_local_portfolio_task_as_dependency_params = dict(
    #             manifest_file_path=self.manifest_file_path,
    #             account_id=task_def.get("account_id"),
    #             region=task_def.get("region"),
    #             portfolio=task_def.get("portfolio"),
    #             organization=task_def.get("organization"),
    #         )
    #
    #         if len(task_def.get("associations", [])) > 0:
    #             create_associations_for_portfolio_task = portfoliomanagement_tasks.CreateAssociationsForSpokeLocalPortfolioTask(
    #                 **create_spoke_local_portfolio_task_as_dependency_params,
    #                 spoke_local_portfolio_name=self.spoke_local_portfolio_name,
    #                 sharing_mode=sharing_mode,
    #                 associations=task_def.get("associations"),
    #                 puppet_account_id=task_def.get("puppet_account_id"),
    #             )
    #             tasks.append(create_associations_for_portfolio_task)
    #
    #         launch_constraints = task_def.get("constraints", {}).get("launch", [])
    #
    #         if product_generation_method == "import":
    #             import_into_spoke_local_portfolio_task = portfoliomanagement_tasks.ImportIntoSpokeLocalPortfolioTask(
    #                 **create_spoke_local_portfolio_task_as_dependency_params,
    #                 spoke_local_portfolio_name=self.spoke_local_portfolio_name,
    #                 sharing_mode=sharing_mode,
    #                 puppet_account_id=task_def.get("puppet_account_id"),
    #             )
    #             tasks.append(import_into_spoke_local_portfolio_task)
    #         else:
    #             copy_into_spoke_local_portfolio_task = portfoliomanagement_tasks.CopyIntoSpokeLocalPortfolioTask(
    #                 **create_spoke_local_portfolio_task_as_dependency_params,
    #                 spoke_local_portfolio_name=self.spoke_local_portfolio_name,
    #                 sharing_mode=sharing_mode,
    #                 puppet_account_id=task_def.get("puppet_account_id"),
    #             )
    #             tasks.append(copy_into_spoke_local_portfolio_task)
    #
    #         if len(launch_constraints) > 0:
    #             create_launch_role_constraints_for_portfolio_task_params = {
    #                 "launch_constraints": launch_constraints,
    #                 "puppet_account_id": task_def.get("puppet_account_id"),
    #             }
    #             create_launch_role_constraints_for_portfolio = portfoliomanagement_tasks.CreateLaunchRoleConstraintsForSpokeLocalPortfolioTask(
    #                 **create_spoke_local_portfolio_task_as_dependency_params,
    #                 **create_launch_role_constraints_for_portfolio_task_params,
    #                 spoke_local_portfolio_name=self.spoke_local_portfolio_name,
    #                 sharing_mode=sharing_mode,
    #                 product_generation_method=product_generation_method,
    #             )
    #             tasks.append(create_launch_role_constraints_for_portfolio)
    #     self.info(f"tasks len are {len(tasks)}")
    #     self.info("generate_tasks out")
    #     return tasks
    #
    # @lru_cache()
    # def get_task_defs(self):
    #     self.info("get_task_defs in")
    #     spoke_local_portfolio_details = self.manifest.get("spoke-local-portfolios").get(
    #         self.spoke_local_portfolio_name
    #     )
    #     configuration = {
    #         "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
    #         "status": spoke_local_portfolio_details.get("status", "shared"),
    #         "portfolio": spoke_local_portfolio_details.get("portfolio"),
    #         "associations": spoke_local_portfolio_details.get("associations", []),
    #         "constraints": spoke_local_portfolio_details.get("constraints", {}),
    #         "depends_on": spoke_local_portfolio_details.get("depends_on", []),
    #         "retry_count": spoke_local_portfolio_details.get("retry_count", 1),
    #         "requested_priority": spoke_local_portfolio_details.get(
    #             "requested_priority", 0
    #         ),
    #         "worker_timeout": spoke_local_portfolio_details.get(
    #             "timeoutInSeconds", constants.DEFAULT_TIMEOUT
    #         ),
    #         "product_generation_method": spoke_local_portfolio_details.get(
    #             "product_generation_method", "copy"
    #         ),
    #         "puppet_account_id": self.puppet_account_id,
    #     }
    #     configuration.update(
    #         manifest_utils.get_configuration_overrides(
    #             self.manifest, spoke_local_portfolio_details
    #         )
    #     )
    #
    #     self.info("get_task_defs out")
    #
    #     return self.manifest.get_task_defs_from_details(
    #         self.puppet_account_id,
    #         True,
    #         self.spoke_local_portfolio_name,
    #         configuration,
    #         "spoke-local-portfolios",
    #     )
    #
    # def run(self):
    #     self.info("started")
    #
    #     task_defs = self.get_task_defs()
    #
    #     self.info("about to get the pre actions")
    #     pre_actions = self.manifest.get_actions_from(
    #         self.spoke_local_portfolio_name, "pre", "spoke-local-portfolios"
    #     )
    #     self.info("about to get the post actions")
    #     post_actions = self.manifest.get_actions_from(
    #         self.spoke_local_portfolio_name, "post", "spoke-local-portfolios"
    #     )
    #
    #     self.info(f"starting pre actions")
    #     yield [
    #         portfoliomanagement_tasks.ProvisionActionTask(
    #             **p, puppet_account_id=self.puppet_account_id,
    #         )
    #         for p in pre_actions
    #     ]
    #     self.info(f"finished pre actions")
    #
    #     self.info(f"starting launches")
    #     yield self.generate_tasks(task_defs)
    #     self.info(f"{self.uid} finished launches")
    #
    #     self.info(f"{self.uid} starting post actions")
    #     yield [
    #         portfoliomanagement_tasks.ProvisionActionTask(
    #             **p, puppet_account_id=self.puppet_account_id,
    #         )
    #         for p in post_actions
    #     ]
    #     self.info(f"{self.uid} finished post actions")
    #
    #     self.write_output(self.params_for_results_display())
    #     self.info("finished")