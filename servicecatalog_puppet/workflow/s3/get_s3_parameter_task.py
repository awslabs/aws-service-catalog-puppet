#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from copy import deepcopy

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks
import jmespath


class GetS3ParameterTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    key = luigi.Parameter()
    jmespath_location = luigi.Parameter()
    default = luigi.Parameter()
    region = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "key": self.key,
            "jmespath_location": self.jmespath_location,
        }

    def run(self):
        with self.spoke_regional_client("s3") as s3:
            object = (
                s3.get_object(
                    Bucket=f"sc-puppet-parameters-{self.account_id}", Key=self.key
                )
                .get("Body")
                .read()
            )
            result = jmespath.search(self.jmespath_location, json.loads(object))
            if result is None:
                print("result was none")
                if self.default is None:
                    raise Exception("Could not find value in the s3 JSON object and there is no default value. Check your JMESPath is correct")
                else:
                    print("defauilt was nmot none")
                    result = self.default
            print("result is", result)
            self.write_output(result)
