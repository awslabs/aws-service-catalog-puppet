import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import tasks as workflow_tasks, dependency


class CodeBuildRunBaseTask(workflow_tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.CODE_BUILD_RUNS


class ExecuteCodeBuildRunTask(CodeBuildRunBaseTask, manifest_tasks.ManifestMixen, dependency.DependenciesMixin):
    code_build_run_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    project_name = luigi.Parameter()
    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "code_build_run_name": self.code_build_run_name,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(
            section_dependencies=self.get_section_dependencies()
        )

    def run(self):
        self.write_output(self.params_for_results_display())


class CodeBuildRunForTask(CodeBuildRunBaseTask, manifest_tasks.ManifestMixen):
    code_build_run_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def get_klass_for_provisioning(self):
        return ExecuteCodeBuildRunTask

    def run(self):
        self.write_output(self.params_for_results_display())


class CodeBuildRunForRegionTask(CodeBuildRunForTask):
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "code_build_run_name": self.code_build_run_name,
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
                self.puppet_account_id, self.section_name, self.code_build_run_name, self.region
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class CodeBuildRunForAccountTask(CodeBuildRunForTask):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "code_build_run_name": self.code_build_run_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_account(
                self.puppet_account_id, self.section_name, self.code_build_run_name, self.account_id
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class CodeBuildRunForAccountAndRegionTask(CodeBuildRunForTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "code_build_run_name": self.code_build_run_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies)

        klass = self.get_klass_for_provisioning()

        for (
                task
        ) in self.manifest.get_tasks_for_launch_and_account_and_region(
            self.puppet_account_id, self.section_name, self.code_build_run_name, self.account_id, self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class CodeBuildRunTask(CodeBuildRunForTask):
    code_build_run_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "code_build_run_name": self.code_build_run_name,
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
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
                self.puppet_account_id, self.section_name, self.code_build_run_name
        ):

            regional_dependencies.append(
                CodeBuildRunForRegionTask(**self.param_kwargs, region=region, )
            )

        for account_id in self.manifest.get_account_ids_used_for_section_item(
                self.puppet_account_id, self.section_name, self.code_build_run_name
        ):
            account_dependencies.append(
                CodeBuildRunForAccountTask(
                    **self.param_kwargs, account_id=account_id,
                )
            )

        for (
                account_id,
                regions,
        ) in self.manifest.get_account_ids_and_regions_used_for_section_item(
            self.puppet_account_id, self.section_name, self.code_build_run_name
        ).items():
            for region in regions:
                account_and_region_dependencies.append(
                    CodeBuildRunForAccountAndRegionTask(
                        **self.param_kwargs,
                        account_id=account_id,
                        region=region,
                    )
                )

        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


class CodeBuildRunsSectionTask(CodeBuildRunBaseTask, manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = dict(
            invocations=[
                CodeBuildRunTask(
                    code_build_run_name=code_build_run_name,
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                )
                for code_build_run_name, code_build_run in self.manifest.get(
                    self.section_name, {}
                ).items()
            ]
        )
        return requirements

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
