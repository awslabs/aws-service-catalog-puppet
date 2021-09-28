#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi
import yaml
from deepmerge import always_merger

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.general import boto3_task
from servicecatalog_puppet.workflow.workspaces import Limits


class GetSSMParamByPathTask(tasks.PuppetTask):
    path = luigi.Parameter()
    recursive = luigi.BoolParameter()

    region = luigi.Parameter(default=None)

    depends_on = luigi.ListParameter(default=[])
    manifest_file_path = luigi.Parameter(default="")
    puppet_account_id = luigi.Parameter(default="")
    spoke_account_id = luigi.Parameter(default="")
    spoke_region = luigi.Parameter(default="")

    def params_for_results_display(self):
        return {
            "path": self.path,
            "recursive": self.recursive,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def resources_used(self):
        identifier = f"{self.region}-{self.puppet_account_id}"
        return [
            (identifier, Limits.SSM_GET_PARAMETER_PER_REGION_OF_ACCOUNT),
        ]

    def requires(self):
        if len(self.depends_on) > 0:
            return dependency.generate_dependency_tasks(
                self.depends_on,
                self.manifest_file_path,
                self.puppet_account_id,
                self.spoke_account_id,
                self.spoke_region,
                self.execution_mode,
            )
        else:
            return []

    def run(self):
        parameters = dict()
        with self.hub_regional_client("ssm") as ssm:
            paginator = ssm.get_paginator("get_parameters_by_path")
            for page in paginator.paginate(Path=self.path, Recursive=self.recursive):
                for parameter in page.get("Parameters", []):
                    parameters[parameter.get("Name")] = dict(
                        Value=parameter.get("Value")
                    )

        self.write_output(parameters)


class GetSSMParamTask(tasks.PuppetTask):
    parameter_name = luigi.Parameter()
    name = luigi.Parameter()
    region = luigi.Parameter(default=None)

    path = luigi.Parameter()
    recursive = luigi.BoolParameter()

    depends_on = luigi.ListParameter(default=[])
    manifest_file_path = luigi.Parameter(default="")
    puppet_account_id = luigi.Parameter(default="")
    spoke_account_id = luigi.Parameter(default="")
    spoke_region = luigi.Parameter(default="")

    def params_for_results_display(self):
        return {
            "parameter_name": self.parameter_name,
            "name": self.name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def resources_used(self):
        if self.path:
            return []
        else:
            identifier = f"{self.region}-{self.puppet_account_id}"
            return [
                (identifier, Limits.SSM_GET_PARAMETER_PER_REGION_OF_ACCOUNT),
            ]

    def requires(self):
        deps = dict()
        if self.path != "":
            deps["ssm"] = GetSSMParamByPathTask(
                path=self.path,
                recursive=self.recursive,
                region=self.region,
                depends_on=self.depends_on,
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                spoke_account_id=self.spoke_account_id,
                spoke_region=self.spoke_region,
            )

        if len(self.depends_on) > 0:
            deps["dependencies"] = dependency.generate_dependency_tasks(
                self.depends_on,
                self.manifest_file_path,
                self.puppet_account_id,
                self.spoke_account_id,
                self.spoke_region,
                self.execution_mode,
            )
        return deps

    def run(self):
        if self.path == "":
            with self.hub_regional_client("ssm") as ssm:
                try:
                    p = ssm.get_parameter(Name=self.name,)
                    self.write_output(
                        {
                            "Name": self.name,
                            "Region": self.region,
                            "Value": p.get("Parameter").get("Value"),
                            "Version": p.get("Parameter").get("Version"),
                        }
                    )
                except ssm.exceptions.ParameterNotFound as e:
                    raise e
        else:
            params = self.load_from_input("ssm")
            self.write_output(params.get(self.name))


class PuppetTaskWithParameters(tasks.PuppetTask):
    def get_all_of_the_params(self):
        all_params = dict()
        always_merger.merge(all_params, tasks.unwrap(self.manifest_parameters))
        always_merger.merge(all_params, tasks.unwrap(self.launch_parameters))
        always_merger.merge(all_params, tasks.unwrap(self.account_parameters))
        return all_params

    def get_parameters_tasks(self):
        ssm_params = dict()
        boto3_params = dict()
        requires = dict(ssm_params=ssm_params, boto3_params=boto3_params,)

        all_params = self.get_all_of_the_params()

        for param_name, param_details in all_params.items():
            if param_details.get("ssm"):
                if param_details.get("default"):
                    del param_details["default"]
                ssm_parameter_name = param_details.get("ssm").get("name")
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::Region}", self.region
                )
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::AccountId}", self.account_id
                )

                ssm_params[param_name] = GetSSMParamTask(
                    parameter_name=param_name,
                    name=ssm_parameter_name,
                    region=param_details.get("ssm").get(
                        "region", config.get_home_region(self.puppet_account_id)
                    ),
                    path=param_details.get("ssm").get("path", ""),
                    recursive=param_details.get("ssm").get("recursive", True),
                    depends_on=param_details.get("ssm").get("depends_on", []),
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                    spoke_account_id=self.account_id,
                    spoke_region=self.region,
                )

            if param_details.get("boto3"):
                if param_details.get("default"):
                    del param_details["default"]

                boto3 = param_details.get("boto3")
                account_id = boto3.get("account_id", self.puppet_account_id).replace(
                    "${AWS::AccountId}", self.account_id
                )

                region = boto3.get(
                    "region", config.get_home_region(self.puppet_account_id)
                ).replace("${AWS::Region}", self.region)

                boto3_params[param_name] = boto3_task.Boto3Task(
                    account_id=account_id,
                    region=region,
                    client=boto3.get("client"),
                    use_paginator=boto3.get("use_paginator", False),
                    call=boto3.get("call"),
                    arguments=boto3.get("arguments", {}),
                    filter=boto3.get("filter")
                    .replace("${AWS::Region}", self.region)
                    .replace("${AWS::AccountId}", self.account_id),
                    requester_task_id=self.task_id,
                    requester_task_family=self.task_family,
                )

        return requires

    def get_parameter_values(self):
        all_params = {}
        self.info(f"collecting all_params")
        p = self.get_all_of_the_params()
        for param_name, param_details in p.items():
            if param_details.get("ssm"):
                with self.input().get("ssm_params").get("ssm_params").get(
                    param_name
                ).open() as f:
                    all_params[param_name] = json.loads(f.read()).get("Value")
            if param_details.get("boto3"):
                with self.input().get("ssm_params").get("boto3_params").get(
                    param_name
                ).open() as f:
                    all_params[param_name] = f.read()
            if param_details.get("default"):
                all_params[param_name] = (
                    param_details.get("default")
                    .replace("${AWS::AccountId}", self.account_id)
                    .replace("${AWS::Region}", self.region)
                )
            if param_details.get("mapping"):
                all_params[param_name] = self.manifest.get_mapping(
                    param_details.get("mapping"), self.account_id, self.region
                )

        self.info(f"finished collecting all_params: {all_params}")
        return all_params

    def terminate_ssm_outputs(self):
        for ssm_param_output in self.ssm_param_outputs:
            param_name = ssm_param_output.get("param_name")
            param_name = param_name.replace("${AWS::Region}", self.region)
            param_name = param_name.replace("${AWS::AccountId}", self.account_id)
            self.info(f"deleting SSM Param: {param_name}")
            with self.hub_client("ssm") as ssm:
                try:
                    # todo push into another task
                    ssm.delete_parameter(Name=param_name,)
                    self.info(f"deleting SSM Param: {param_name}")
                except ssm.exceptions.ParameterNotFound:
                    self.info(f"SSM Param: {param_name} not found")
