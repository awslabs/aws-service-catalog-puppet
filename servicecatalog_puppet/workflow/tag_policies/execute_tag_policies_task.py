#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.tag_policies import tag_policies_base_task
from servicecatalog_puppet.workflow.tag_policies import do_execute_tag_policies_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class ExecuteTagPoliciesTask(
    tag_policies_base_task.TagPoliciesBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    tag_policy_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()
    ou_name = luigi.Parameter()

    content = luigi.DictParameter()
    description = luigi.Parameter()

    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "tag_policy_name": self.tag_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "ou_name": self.ou_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(section_dependencies=self.get_section_dependencies())

    def run(self):
        yield do_execute_tag_policies_task.DoExecuteTagPoliciesTask(
            manifest_file_path=self.manifest_file_path,
            tag_policy_name=self.tag_policy_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            account_id=self.account_id,
            ou_name=self.ou_name,
            content=self.content,
            description=self.description,
            requested_priority=self.requested_priority,
        )
        self.write_output(self.params_for_results_display())
