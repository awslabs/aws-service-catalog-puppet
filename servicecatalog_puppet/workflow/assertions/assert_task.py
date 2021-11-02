#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.assertions import assertion_base_task
from servicecatalog_puppet.workflow.assertions import do_assert_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class AssertTask(
    assertion_base_task.AssertionBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    assertion_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()
    execution = luigi.Parameter()

    expected = luigi.DictParameter()
    actual = luigi.DictParameter()

    requested_priority = luigi.IntParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "assertion_name": self.assertion_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = {"section_dependencies": self.get_section_dependencies()}
        return requirements

    def run(self):
        yield do_assert_task.DoAssertTask(
            manifest_file_path=self.manifest_file_path,
            assertion_name=self.assertion_name,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
            expected=self.expected,
            actual=self.actual,
            requested_priority=self.requested_priority,
            execution=self.execution,
        )
        self.write_output(self.params_for_results_display())
