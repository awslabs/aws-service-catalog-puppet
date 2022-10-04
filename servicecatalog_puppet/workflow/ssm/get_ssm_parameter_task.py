#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import luigi

from servicecatalog_puppet.workflow.dependencies import tasks


class GetSSMParameterTask(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    param_name = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        parameter_name_to_use = self.param_name.replace(
            "${AWS::Region}", self.region
        ).replace("${AWS::AccountId}", self.account_id)
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

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "path": self.path,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        path = self.path.replace("${AWS::Region}", self.region).replace(
            "${AWS::AccountId}", self.account_id
        )
        parameters = dict()
        with self.spoke_regional_client("ssm") as ssm:
            paginator = ssm.get_paginator("get_parameters_by_path")
            for page in paginator.paginate(Path=path, Recursive=True):
                for parameter in page.get("Parameters", []):
                    parameters[parameter.get("Name")] = parameter
        self.write_output(parameters)
