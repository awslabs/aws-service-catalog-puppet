#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.tag_policies import tag_policies_base_task
from servicecatalog_puppet.workflow.tag_policies import execute_tag_policies_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class TagPoliciesForTask(
    tag_policies_base_task.TagPoliciesBaseTask, manifest_mixin.ManifestMixen,
):
    tag_policies_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "tag_policies_name": self.tag_policies_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return execute_tag_policies_task.ExecuteTagPoliciesTask

    def run(self):
        self.write_output(self.params_for_results_display())
