#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi


class GenericForAccountAndRegionTask:
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
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
            "account_id": self.account_id,
            "region": self.region,
            "single_account": self.single_account,
        }
        for task in self.manifest.get_tasks_for_launch_and_account_and_region(**a):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
