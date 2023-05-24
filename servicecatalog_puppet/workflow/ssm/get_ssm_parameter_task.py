#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class GetSSMParameterTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    param_name = luigi.Parameter()
    region = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
        }

    def get_parameter_name_to_use(self):
        return self.param_name.replace("${AWS::Region}", self.region).replace(
            "${AWS::AccountId}", self.account_id
        )

    def run(self):
        parameter_name_to_use = self.get_parameter_name_to_use()
        result = {}
        with self.spoke_regional_client("ssm") as ssm:
            try:
                parameter = ssm.get_parameter(Name=parameter_name_to_use)
                result = {parameter_name_to_use: parameter.get("Parameter")}
            except ssm.exceptions.ParameterNotFound:
                pass

        self.write_output(result)


class GetSSMParameterByPathTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    path = luigi.Parameter()
    region = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "path": self.path,
        }

    def run(self):
        parameters = dict()
        with self.spoke_regional_client("ssm") as ssm:
            paginator = ssm.get_paginator("get_parameters_by_path")
            for page in paginator.paginate(
                Path=self.get_parameter_path_to_use(), Recursive=True
            ):
                for parameter in page.get("Parameters", []):
                    parameters[parameter.get("Name")] = parameter
        self.write_output(parameters)

    def get_parameter_path_to_use(self):
        return self.path.replace("${AWS::Region}", self.region).replace(
            "${AWS::AccountId}", self.account_id
        )
