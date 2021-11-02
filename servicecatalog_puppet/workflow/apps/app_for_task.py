#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.apps import app_base_task
from servicecatalog_puppet.workflow.apps import provision_app_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class AppForTask(app_base_task.AppBaseTask, manifest_mixin.ManifestMixen):
    app_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "app_name": self.app_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        if self.is_dry_run or self.execution_mode == constants.EXECUTION_MODE_SPOKE:
            raise Exception("Dry run and spoke execution mode are not yet supported")
        return provision_app_task.ProvisionAppTask

    def run(self):
        self.write_output(self.params_for_results_display())
