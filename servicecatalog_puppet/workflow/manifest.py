import os
from functools import lru_cache

import luigi
import yaml

from servicecatalog_puppet import manifest_utils

from servicecatalog_puppet.workflow import tasks


class ManifestTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
        }

    def run(self):
        self.info("started")
        with open(self.manifest_file_path, "r") as m:
            manifest = manifest_utils.load(m, self.puppet_account_id)
        self.write_output(manifest)
        self.info("Finished")


class ManifestMixen(object):
    manifest_file_path = luigi.Parameter()

    @property
    @lru_cache
    def manifest(self):
        content = open(self.manifest_file_path, "r").read()
        return manifest_utils.Manifest(yaml.safe_load(content))


class SectionTask(tasks.PuppetTask, ManifestMixen):
    # class SectionTask(tasks.PuppetTask, ManifestMixen):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()
    execution_mode = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    @property
    @lru_cache
    def manifest(self):
        content = open(self.manifest_file_path, "r").read()
        return manifest_utils.Manifest(yaml.safe_load(content))
