#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import deepdiff
import jmespath
import luigi
from deepmerge import always_merger

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.assertions import assertion_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


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

    def run(self):
        config = self.actual.get("config")
        with self.spoke_regional_client(config.get("client")) as client:
            if config.get("use_paginator"):
                paginator = client.get_paginator(config.get("call"))
                result = dict()
                for page in paginator.paginate(**config.get("arguments")):
                    always_merger.merge(result, page)
            else:
                f = getattr(client, config.get("call"))
                result = f(**config.get("arguments"))

            actual_result = jmespath.search(config.get("filter"), result)
            expected_result = self.expected.get("config").get("value")
            if isinstance(expected_result, tuple):
                expected_result = list(expected_result)

            ddiff = deepdiff.DeepDiff(actual_result, expected_result, ignore_order=True)
            if len(ddiff.keys()) > 0:
                raise Exception(ddiff)
            else:
                self.write_output(self.params_for_results_display())
