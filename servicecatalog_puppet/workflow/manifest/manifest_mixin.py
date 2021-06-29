from functools import lru_cache

import luigi
import yaml

from servicecatalog_puppet import manifest_utils


class ManifestMixen(object):
    manifest_file_path = luigi.Parameter()

    @property
    @lru_cache()
    def manifest(self):
        content = open(self.manifest_file_path, "r").read()
        return manifest_utils.Manifest(yaml.safe_load(content))
