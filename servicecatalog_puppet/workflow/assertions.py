import luigi
import jmespath
import deepdiff
from deepmerge import always_merger

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import tasks as workflow_tasks
from servicecatalog_puppet.workflow import dependency


class AssertionBaseTask(workflow_tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.ASSERTIONS


class AssertTask(
    AssertionBaseTask, manifest_tasks.ManifestMixen, dependency.DependenciesMixin
):
    assertion_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    expected = luigi.DictParameter()
    actual = luigi.DictParameter()

    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = {"section_dependencies": self.get_section_dependencies()}
        return requirements

    def run(self):
        yield DoAssertTask(
            manifest_file_path=self.manifest_file_path,
            assertion_name=self.assertion_name,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
            expected=self.expected,
            actual=self.actual,
            requested_priority=self.requested_priority,
        )
        self.write_output(self.params_for_results_display())


class DoAssertTask(
    AssertionBaseTask, manifest_tasks.ManifestMixen, dependency.DependenciesMixin
):
    assertion_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    expected = luigi.DictParameter()
    actual = luigi.DictParameter()

    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        config = self.actual.get("config")
        with self.spoke_regional_client(config.get("client")) as client:
            if config.get("use_paginator"):
                paginator = client.get_paginator(config.get("call"))
                result = dict()
                for page in paginator.paginate(**config.get("arguments")):
                    always_merger.merge(result, page)
            else:
                f = getattr(client, config.get("call"))
                result = f(**config.get("arguments"))

            actual_result = jmespath.search(config.get("filter"), result)
            expected_result = self.expected.get("config").get("value")
            if isinstance(expected_result, tuple):
                expected_result = list(expected_result)

            ddiff = deepdiff.DeepDiff(actual_result, expected_result, ignore_order=True)
            if len(ddiff.keys()) > 0:
                raise Exception(ddiff)
            else:
                self.write_output(self.params_for_results_display())


class AssertionForTask(AssertionBaseTask, manifest_tasks.ManifestMixen):
    assertion_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return AssertTask

    def run(self):
        self.write_output(self.params_for_results_display())


class AssertionForRegionTask(AssertionForTask):
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
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
            self.puppet_account_id, self.section_name, self.assertion_name, self.region
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class AssertionForAccountTask(AssertionForTask):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_account(
            self.puppet_account_id,
            self.section_name,
            self.assertion_name,
            self.account_id,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class AssertionForAccountAndRegionTask(AssertionForTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
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
            self.assertion_name,
            self.account_id,
            self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class AssertionTask(AssertionForTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
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
            self.puppet_account_id, self.section_name, self.assertion_name
        ):
            regional_dependencies.append(
                AssertionForRegionTask(**self.param_kwargs, region=region,)
            )

        for account_id in self.manifest.get_account_ids_used_for_section_item(
            self.puppet_account_id, self.section_name, self.assertion_name
        ):
            account_dependencies.append(
                AssertionForAccountTask(**self.param_kwargs, account_id=account_id,)
            )

        for (
            account_id,
            regions,
        ) in self.manifest.get_account_ids_and_regions_used_for_section_item(
            self.puppet_account_id, self.section_name, self.assertion_name
        ).items():
            for region in regions:
                account_and_region_dependencies.append(
                    AssertionForAccountAndRegionTask(
                        **self.param_kwargs, account_id=account_id, region=region,
                    )
                )

        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


class AssertionsSectionTask(AssertionBaseTask, manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = dict(
            invocations=[
                AssertionTask(
                    assertion_name=assertion_name,
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                )
                for assertion_name, assertion in self.manifest.get(
                    self.section_name, {}
                ).items()
            ]
        )
        return requirements

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
