#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import luigi
from deepmerge import always_merger
import jmespath

from servicecatalog_puppet.workflow import tasks


class Boto3Task(tasks.PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    client = luigi.Parameter()
    use_paginator = luigi.BoolParameter()
    call = luigi.Parameter()
    arguments = luigi.DictParameter()
    filter = luigi.Parameter()

    requester_task_id = luigi.Parameter()
    requester_task_family = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "client": self.client,
            "use_paginator": self.use_paginator,
            "call": self.call,
            "requester_task_id": self.requester_task_id,
            "requester_task_family": self.requester_task_family,
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
