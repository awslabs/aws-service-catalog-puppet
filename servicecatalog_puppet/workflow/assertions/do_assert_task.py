#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import deepdiff
from datetime import datetime
import luigi


from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.assertions import assertion_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.general import boto3_task


class DoAssertTask(
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
        config = self.actual.get("config")
        return dict(
            result=boto3_task.Boto3Task(
                account_id=self.account_id,
                region=self.region,
                client=config.get("client"),
                use_paginator=config.get("use_paginator"),
                call=config.get("call"),
                arguments=config.get("arguments"),
                filter=config.get("filter"),
                requester_task_id=self.task_id,
                requester_task_family=self.task_family,
            )
        )

    def run(self):
        actual_result = self.load_from_input("result")
        expected_result = self.expected.get("config").get("value")
        if isinstance(expected_result, tuple):
            expected_result = list(expected_result)
        elif isinstance(actual_result, str):
            expected_result = expected_result.strip()

        ddiff = deepdiff.DeepDiff(actual_result, expected_result, ignore_order=True)
        if len(ddiff.keys()) > 0:
            raise Exception(ddiff)
        else:
            self.write_output(self.params_for_results_display())
