#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import deepdiff
import jmespath
import luigi
from deepmerge import always_merger

from servicecatalog_puppet.workflow.dependencies import tasks


class DoAssertTask(tasks.TaskWithParameters):
    assertion_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

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

    def get_actual_result(self):
        config = self.actual.get("config")
        client = config.get("client")
        use_paginator = config.get("use_paginator")
        call = config.get("call")
        arguments = config.get("arguments")
        filter = config.get("filter")

        with self.spoke_regional_client(client) as client:
            if use_paginator:
                paginator = client.get_paginator(call)
                result = dict()
                for page in paginator.paginate(**arguments):
                    always_merger.merge(result, page)
            else:
                f = getattr(client, call)
                result = f(**arguments)

        actual_result = jmespath.search(filter, result)
        if isinstance(actual_result, str):
            return actual_result.strip()
        else:
            return actual_result

    def run(self):
        actual_result = self.get_actual_result()
        expected_result = self.expected.get("config").get("value")
        if isinstance(expected_result, tuple):
            expected_result = list(expected_result)
        elif isinstance(actual_result, str):
            expected_result = expected_result.strip()

        ddiff = deepdiff.DeepDiff(actual_result, expected_result, ignore_order=True)
        if len(ddiff.keys()) > 0:
            raise Exception(ddiff)
        else:
            self.write_empty_output()
