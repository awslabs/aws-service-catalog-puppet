#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from functools import lru_cache

import luigi
import yaml

from servicecatalog_puppet import constants
from servicecatalog_puppet import manifest_utils


class ManifestMixen(object):
    manifest_file_path = luigi.Parameter()

    @property
    def status(self):
        return (
            self.manifest.get(self.section_name)
            .get(self.item_name)
            .get("status", constants.PROVISIONED)
        )

    @property
    @lru_cache()
    def manifest(self):
        content = open(self.manifest_file_path, "r").read()
        return manifest_utils.Manifest(yaml.safe_load(content))
