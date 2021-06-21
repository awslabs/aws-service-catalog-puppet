from functools import lru_cache

import luigi
import yaml

from servicecatalog_puppet import manifest_utils
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet import constants


class ManifestMixen(object):
    manifest_file_path = luigi.Parameter()

    @property
    @lru_cache()
    def manifest(self):
        content = open(self.manifest_file_path, "r").read()
        return manifest_utils.Manifest(yaml.safe_load(content))


class SectionTask(tasks.PuppetTask, ManifestMixen):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    @property
    @lru_cache()
    def manifest(self):
        content = open(self.manifest_file_path, "r").read()
        return manifest_utils.Manifest(yaml.safe_load(content))

    def handle_requirements_for(
        self,
        name,
        details,
        section_name_singular,
        section_name_plural,
        is_in_spoke_execution_mode,
        for_region_task_klass,
        for_account_task_klass,
        for_account_and_region_task_klass,
        task_klass,
        kwargs_to_use,
    ):
        if is_in_spoke_execution_mode:
            if section_name_plural == constants.LAUNCHES:
                if details.get("execution") != constants.EXECUTION_MODE_SPOKE:
                    return []
        else:
            if details.get("execution") == constants.EXECUTION_MODE_SPOKE:
                from servicecatalog_puppet.workflow import launch

                dependencies = list()
                for account_id in self.manifest.get_account_ids_used_for_section_item(
                    self.puppet_account_id, section_name_plural, name
                ):
                    dependencies.append(
                        launch.RunDeployInSpokeTask(
                            manifest_file_path=kwargs_to_use.get("manifest_file_path"),
                            puppet_account_id=self.puppet_account_id,
                            account_id=account_id,
                        )
                    )
                return dependencies

        dependencies = list()

        affinities_used = dict()
        is_a_dependency = False

        for manifest_section_name in constants.ALL_SECTION_NAMES:
            for n, d in self.manifest.get(manifest_section_name, {}).items():
                for dep in d.get("depends_on", []):
                    if (
                        dep.get("type") == section_name_singular
                        and dep.get("name") == name
                    ):
                        is_a_dependency = True
                        affinities_used[dep.get("affinity")] = True

        if is_a_dependency:
            if affinities_used.get(constants.AFFINITY_REGION):
                for region in self.manifest.get_regions_used_for_section_item(
                    self.puppet_account_id, section_name_plural, name
                ):
                    dependencies.append(
                        for_region_task_klass(**kwargs_to_use, region=region,)
                    )

            if affinities_used.get(constants.AFFINITY_ACCOUNT):
                for account_id in self.manifest.get_account_ids_used_for_section_item(
                    self.puppet_account_id, section_name_plural, name
                ):
                    dependencies.append(
                        for_account_task_klass(**kwargs_to_use, account_id=account_id,)
                    )

            if affinities_used.get(constants.AFFINITY_ACCOUNT_AND_REGION):
                for (
                    account_id,
                    regions,
                ) in self.manifest.get_account_ids_and_regions_used_for_section_item(
                    self.puppet_account_id, section_name_plural, name
                ).items():
                    for region in regions:
                        dependencies.append(
                            for_account_and_region_task_klass(
                                **kwargs_to_use, account_id=account_id, region=region,
                            )
                        )

            if affinities_used.get(section_name_singular):
                dependencies.append(task_klass(**kwargs_to_use))

        else:
            dependencies.append(task_klass(**kwargs_to_use))

        return dependencies
