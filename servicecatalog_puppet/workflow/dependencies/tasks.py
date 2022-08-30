#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging

import luigi
from deepmerge import always_merger

from servicecatalog_puppet import constants
from servicecatalog_puppet import manifest_utils
from servicecatalog_puppet import yaml_utils
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    create,
)

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


class TaskWithReference(tasks.PuppetTask):
    task_reference = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()
    puppet_account_id = luigi.Parameter()

    def requires(self):
        return dict(reference_dependencies=self.get_dependencies_for_task_reference())

    def get_output_from_reference_dependency(self, reference):
        return json.loads(
            self.input().get("reference_dependencies").get(reference).open("r").read()
        )

    def get_dependencies_for_task_reference(self):
        dependencies = dict()
        reference = yaml_utils.load(
            open(self.manifest_task_reference_file_path, "r").read()
        ).get("all_tasks")
        this_task = reference.get(self.task_reference)
        if this_task is None:
            raise Exception(f"Did not find {self.task_reference} within reference")
        for dependency_by_reference in this_task.get("dependencies_by_reference", []):
            dependency_by_reference_params = reference.get(dependency_by_reference)
            if dependency_by_reference_params is None:
                raise Exception(
                    f"{self.task_reference} has a dependency: {dependency_by_reference} unsatisfied by the manifest task reference"
                )
            t_reference = dependency_by_reference_params.get("task_reference")
            dependencies[t_reference] = create(
                self.manifest_task_reference_file_path,
                self.puppet_account_id,
                dependency_by_reference_params,
            )
        return dependencies

    @property
    def uid(self):
        return f"{self.task_reference}"

    def get_output_location_path(self):
        return f"output/{self.__class__.__name__}/{self.task_reference}/{self.params_for_results_display().get('cache_invalidator', 'latest')}.{self.output_suffix}"


class TaskWithParameters(TaskWithReference):
    def get_merged_launch_account_and_manifest_parameters(self):
        content = open(self.manifest_file_path, "r").read()
        manifest = manifest_utils.Manifest(yaml_utils.load(content))

        result = dict()
        launch_parameters = (
            manifest.get(self.section_name).get(self.item_name).get("parameters", {})
        )
        manifest_parameters = manifest.get("parameters")
        account_parameters = manifest.get_account(self.account_id).get("parameters")

        always_merger.merge(result, manifest_parameters)
        always_merger.merge(result, launch_parameters)
        always_merger.merge(result, account_parameters)
        return result

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

                if requested_param_details.get("path"):
                    required_task_reference = f"{constants.SSM_PARAMETERS_WITH_A_PATH}-{requested_param_account_id}-{requested_param_region}-{requested_param_details.get('path')}"
                else:
                    required_task_reference = f"{constants.SSM_PARAMETERS}-{requested_param_account_id}-{requested_param_region}-{requested_param_name}"

                parameter_task_output = json.loads(  # TODO optimise
                    self.input()
                    .get("reference_dependencies")
                    .get(required_task_reference)
                    .open("r")
                    .read()
                )

                if parameter_task_output.get(requested_param_name):
                    all_params[param_name] = parameter_task_output.get(
                        requested_param_name,
                    ).get("Value")
                elif requested_param_details.get("default"):
                    all_params[param_name] = requested_param_details.get("default")
                else:
                    raise Exception(
                        "Could not find parameter value and no default was set"
                    )

            if param_details.get("boto3"):
                requested_param_details = param_details.get("boto3")
                boto3_task_account_id = requested_param_details.get("account_id")
                boto3_task_region = requested_param_details.get("region")
                if param_details.get("cloudformation_stack_output"):
                    boto3_section = constants.STACKS
                    boto3_item = param_details["cloudformation_stack_output"][
                        "stack_name"
                    ]
                elif param_details.get("servicecatalog_provisioned_product_output"):
                    boto3_section = constants.LAUNCHES
                    boto3_item = param_details[
                        "servicecatalog_provisioned_product_output"
                    ]["provisioned_product_name"]
                else:
                    boto3_section = constants.BOTO3_PARAMETERS
                    boto3_item = ""  # TODO FIXME

                task_ref = f"{constants.BOTO3_PARAMETERS}-{boto3_section}-{boto3_item}-{param_name}-{boto3_task_account_id}-{boto3_task_region}"
                task_ref = (
                    task_ref.replace("${AWS::AccountId}", self.account_id)
                    .replace("${AWS::PuppetAccountId}", self.puppet_account_id)
                    .replace("${AWS::Region}", self.region)
                )
                parameter_task_output = json.loads(  # TODO optimise
                    self.input()
                    .get("reference_dependencies")
                    .get(task_ref)
                    .open("r")
                    .read()
                )
                all_params[param_name] = parameter_task_output

            if param_details.get("default"):
                all_params[param_name] = (
                    param_details.get("default")
                    .replace("${AWS::AccountId}", self.account_id)
                    .replace("${AWS::Region}", self.region)
                )
            if param_details.get("mapping"):
                content = open(self.manifest_file_path, "r").read()
                manifest = manifest_utils.Manifest(yaml_utils.load(content))

                all_params[param_name] = manifest.get_mapping(
                    param_details.get("mapping"), self.account_id, self.region
                )
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


def unwrap(what):
    if hasattr(what, "get_wrapped"):
        return unwrap(what.get_wrapped())

    if isinstance(what, dict):
        thing = dict()
        for k, v in what.items():
            thing[k] = unwrap(v)
        return thing

    if isinstance(what, tuple):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    if isinstance(what, list):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    return what
