#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier= Apache-2.0
from servicecatalog_puppet.workflow import tasks
import luigi

class GetSSMParameterTask(tasks.PuppetTask):
    account_id= luigi.Parameter()
    param_name= luigi.Parameter()
    region= luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"ssm.get_parameter_{self.account_id}_{self.region}",
        ]

    def run(self):
        with self.spoke_regional_client('ssm') as ssm:

        raise Exception("really?")
        self.write_output("done")