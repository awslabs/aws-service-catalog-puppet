#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from servicecatalog_puppet import serialisation_utils

import jmespath
import luigi
from deepmerge import always_merger

from servicecatalog_puppet.workflow.dependencies import tasks

remove_punctuation_map = dict((ord(char), None) for char in '\/*?:"<>|\n')


def hash(what):
    return json.dumps(tasks.unwrap(what), indent=0).translate(remove_punctuation_map)


class Boto3Task(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    client = luigi.Parameter()
    use_paginator = luigi.BoolParameter()
    call = luigi.Parameter()
    arguments = luigi.DictParameter()
    filter = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "client": self.client,
            "use_paginator": self.use_paginator,
            "call": self.call,
            "arguments": hash(self.arguments),
            "filter": hash(self.filter),
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        with self.spoke_regional_client(self.client) as client:
            if self.use_paginator:
                paginator = client.get_paginator(self.call)
                result = dict()
                for page in paginator.paginate(**self.arguments):
                    always_merger.merge(result, page)
            else:
                f = getattr(client, self.call)
                result = f(**self.arguments)

        actual_result = jmespath.search(self.filter, result)
        if isinstance(actual_result, str):
            self.write_output(actual_result.strip())
        else:
            self.write_output(actual_result)
