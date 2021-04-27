from functools import lru_cache

import luigi
import yaml

from servicecatalog_puppet import manifest_utils
from servicecatalog_puppet.workflow import tasks


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
