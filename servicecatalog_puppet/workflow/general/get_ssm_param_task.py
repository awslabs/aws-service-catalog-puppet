#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi
from deepmerge import always_merger

from servicecatalog_puppet import yaml_utils
from servicecatalog_puppet import config
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)
from servicecatalog_puppet import constants
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
                self.ou_name if hasattr(self, "ou_name") else "",
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


class GetSSMParamIndividuallyTask(tasks.PuppetTask):
    name = luigi.Parameter()
    default_value = luigi.Parameter()
    region = luigi.Parameter(default=None)

    puppet_account_id = luigi.Parameter(default="")

    def params_for_results_display(self):
        return {
            "name": self.name,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def resources_used(self):
        identifier = f"{self.region}-{self.puppet_account_id}"
        return [
            (identifier, Limits.SSM_GET_PARAMETER_PER_REGION_OF_ACCOUNT),
        ]

    def run(self):
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
                if self.default_value is not None:
                    self.write_output(
                        {
                            "Name": self.name,
                            "Region": self.region,
                            "Value": self.default_value,
                            "Version": 0,
                        }
                    )
                else:
                    raise e


class GetSSMParamTask(tasks.PuppetTask):
    parameter_name = luigi.Parameter()
    name = luigi.Parameter()
    default_value = luigi.Parameter()
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
                self.ou_name if hasattr(self, "ou_name") else "",
                self.spoke_region,
                self.execution_mode,
            )
        return deps

    def run(self):
        if self.path == "":
            result = yield GetSSMParamIndividuallyTask(
                name=self.name,
                default_value=self.default_value,
                region=self.region,
                puppet_account_id=self.puppet_account_id,
            )
            self.write_output(
                result.open("r").read(), skip_json_dump=True,
            )
        else:
            params = self.load_from_input("ssm")
            self.write_output(params.get(self.name))


class PuppetTaskWithParameters(tasks.PuppetTask):
    def get_merged_launch_account_and_manifest_parameters(self):
        result = dict()
        launch_parameters = (
            self.manifest.get(self.section_name)
            .get(self.item_name)
            .get("parameters", {})
        )
        manifest_parameters = self.manifest.get("parameters")
        account_parameters = self.manifest.get_account(self.account_id).get(
            "parameters"
        )

        always_merger.merge(result, manifest_parameters)
        always_merger.merge(result, launch_parameters)
        always_merger.merge(result, account_parameters)
        return result

    def get_all_of_the_params(self):
        raise Exception("THIS SHOULD BE REMOVED!!!!")
        # TODO remove
        all_params = dict()
        always_merger.merge(all_params, tasks.unwrap(self.manifest_parameters))
        always_merger.merge(all_params, tasks.unwrap(self.launch_parameters))
        always_merger.merge(all_params, tasks.unwrap(self.account_parameters))
        return all_params

    def get_parameters_tasks(self):
        return get_dependencies_for_task_reference(
            self.manifest_task_reference_file_path, self.task_reference
        )

    def get_parameter_values(self):
        all_params = {}
        self.info(f"collecting all_params")
        p = self.get_merged_launch_account_and_manifest_parameters()
        for param_name, param_details in p.items():
            if param_details.get("ssm"):
                requested_param_details = param_details.get("ssm")
                requested_param_region = requested_param_details.get(
                    "region", constants.HOME_REGION
                )
                requested_param_account_id = requested_param_details.get(
                    "account_id", self.puppet_account_id
                )

                requested_param_name = (
                    requested_param_details.get("name")
                    .replace("${AWS::AccountId}", self.account_id)
                    .replace("${AWS::Region}", self.region)
                )

                required_task_reference = f"ssm_parameters-{requested_param_account_id}-{requested_param_region}-{requested_param_name}"

                print(self.input())
                reference_dependencies = self.input().get("reference_dependencies")
                parameter_task_output = json.loads(
                    self.input()
                    .get("reference_dependencies")
                    .get(required_task_reference)
                    .open("r")
                    .read()
                )

                all_params[param_name] = (
                    parameter_task_output.get(requested_param_name)
                    .get("Parameter")
                    .get("Value")
                )

            if param_details.get("boto3"):
                with self.input().get("ssm_params").get("boto3_params").get(
                    param_name
                ).open() as f:
                    all_params[param_name] = json.loads(f.read())
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
