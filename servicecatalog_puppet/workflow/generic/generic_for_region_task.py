#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants


class GenericForRegionTask:
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
            self.item_identifier: self.item_name,
        }

    def requires(self):
        dependencies = list()
        these_dependencies = list()
        requirements = dict(
            dependencies=dependencies, these_dependencies=these_dependencies,
        )

        klass = self.get_klass_for_provisioning()

        a = {
            "puppet_account_id": self.puppet_account_id,
            "section_name": self.section_name,
            self.item_identifier: self.item_name,
            "region": self.region,
            "single_account": self.single_account,
        }
        for task in self.manifest.get_tasks_for_launch_and_region(**a):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        item = self.manifest.get(self.section_name).get(self.item_name)
        for depends_on in item.get("depends_on", []):
            if depends_on.get("type") == self.section_name:
                if depends_on.get(constants.AFFINITY) == "region":
                    b = {
                        "manifest_file_path": self.manifest_file_path,
                        self.item_identifier: depends_on.get("name"),
                        "puppet_account_id": self.puppet_account_id,
                        "region": self.region,
                    }
                    these_dependencies.append(self.__class__(**b))

        return requirements
