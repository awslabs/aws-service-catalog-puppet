#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.assertions import assertion_for_task


class AssertionForRegionTask(assertion_for_task.AssertionForTask):
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
            self.puppet_account_id,
            self.section_name,
            self.assertion_name,
            self.region,
            single_account=self.single_account,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements
