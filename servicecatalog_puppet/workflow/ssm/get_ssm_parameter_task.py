#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier= Apache-2.0
from servicecatalog_puppet.workflow import tasks
import luigi

from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)
from servicecatalog_puppet.workflow.workspaces import Limits


class GetSSMParameterTask(tasks.PuppetTask):  # TODO add by path parameters
    # TODO add support for default_value
    puppet_account_id = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    task_reference = luigi.Parameter()
    account_id = luigi.Parameter()
    param_name = luigi.Parameter()
    region = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def resources_used(self):
        uniq = f"{self.region}-{self.puppet_account_id}"
        return [
            (uniq, Limits.SSM_GET_PARAMETER_PER_REGION_OF_ACCOUNT),
        ]

    def requires(self):
        return get_dependencies_for_task_reference(
            self.manifest_task_reference_file_path,
            self.task_reference,
            self.puppet_account_id,
        )

    def run(self):
        parameter_name_to_use = self.param_name.replace(
            "${AWS::Region}", self.region
        ).replace("${AWS::AccountId}", self.account_id)
        with self.spoke_regional_client("ssm") as ssm:
            parameter = ssm.get_parameter(Name=parameter_name_to_use)
        result = {parameter_name_to_use: parameter}
        self.write_output(result)
