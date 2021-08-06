#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.assertions import assert_task
from servicecatalog_puppet.workflow.assertions import assertion_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class AssertionForTask(
    assertion_base_task.AssertionBaseTask, manifest_mixin.ManifestMixen
):
    assertion_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return assert_task.AssertTask

    def run(self):
        self.write_output(self.params_for_results_display())
