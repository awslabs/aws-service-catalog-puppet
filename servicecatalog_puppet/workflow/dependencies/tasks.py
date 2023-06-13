#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import functools
import logging

import luigi
from deepmerge import always_merger

from servicecatalog_puppet import constants, manifest_utils, serialisation_utils
from servicecatalog_puppet.commands import graph
from servicecatalog_puppet.waluigi.task_mixins import (
    io_mixin,
    task_executor_mixin,
)
from servicecatalog_puppet.workflow.dependencies import task_factory
from servicecatalog_puppet.workflow.task_mixins import (
    client_mixin,
    env_var_mixin,
)


logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


class TaskWithReference(
    task_executor_mixin.TaskExecutorMixin,
    env_var_mixin.EnvVarMixin,
    io_mixin.IOMixin,
    luigi.Task,
    client_mixin.ClientMixin,
):
    task_reference = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()
    puppet_account_id = luigi.Parameter()
    manifest_files_path = luigi.Parameter()

    cachable_level = constants.CACHE_LEVEL_DEFAULT

    def get_expanded_manifest_file_path(self):
        return f"{self.manifest_files_path}/manifest-expanded.yaml"

    def get_from_manifest(self, section_name, item_name):
        with open(self.get_expanded_manifest_file_path(), "r") as f:
            m = serialisation_utils.load(f.read())
            return m[section_name][item_name]

    def requires(self):
        return dict(reference_dependencies=self.dependencies_for_task_reference())

    def read_from_input(self, input_name):
        with self.input().get(input_name).open("rb") as f:
            return f.read()

    def load_from_input(self, input_name):
        return serialisation_utils.json_loads(self.read_from_input(input_name))

    def get_output_from_reference_dependency(self, reference):
        with self.input().get("reference_dependencies").get(reference).open("r") as f:
            content = f.read()
        return serialisation_utils.json_loads(content)

    def get_attribute_from_output_from_reference_dependency(self, attribute, reference):
        return self.get_output_from_reference_dependency(reference).get(attribute)

    def get_output_from_reference_dependency_raw(self, reference):
        f = self.input().get("reference_dependencies").get(reference).open("r")
        content = f.read()
        f.close()
        return content

    @functools.lru_cache(maxsize=32)
    def get_task_from_reference(self, task_reference):
        f = open(
            f"{self.manifest_files_path}/tasks/{graph.escape(task_reference)}.json", "r"
        )
        c = f.read()
        f.close()
        return serialisation_utils.load_as_json(c)

    @functools.lru_cache(maxsize=32)
    def dependencies_for_task_reference(self):
        dependencies = dict()

        this_task = self.get_task_from_reference(self.task_reference)
        if this_task is None:
            raise Exception(f"Did not find {self.task_reference} within reference")
        for dependency_by_reference in this_task.get("dependencies_by_reference", []):
            dependency_by_reference_params = self.get_task_from_reference(
                dependency_by_reference
            )
            if dependency_by_reference_params is None:
                raise Exception(
                    f"{self.task_reference} has a dependency: {dependency_by_reference} unsatisfied by the manifest task reference"
                )
            t_reference = dependency_by_reference_params.get("task_reference")
            dependencies[t_reference] = task_factory.create(
                self.manifest_files_path,
                self.manifest_task_reference_file_path,
                self.puppet_account_id,
                dependency_by_reference_params,
            )
        return dependencies

    def info(self, message):
        logger.info(f"{self.task_reference}: {message}")

    def debug(self, message):
        logger.debug(f"{self.task_reference}: {message}")

    def error(self, message):
        logger.error(f"{self.task_reference}: {message}")

    def warning(self, message):
        logger.warning(f"{self.task_reference}: {message}")


class TaskWithReferenceAndCommonParameters(TaskWithReference):
    region = luigi.Parameter()
    account_id = luigi.Parameter()


class TaskWithParameters(TaskWithReference):
    def get_merged_launch_account_and_manifest_parameters(self):
        content = open(self.manifest_file_path, "r").read()
        manifest = manifest_utils.Manifest(serialisation_utils.load(content))

        result = dict()
        launch_parameters = (
            manifest.get(self.section_name).get(self.item_name).get("parameters", {})
        )
        manifest_parameters = manifest.get("parameters")
        account_parameters = manifest.get_account(self.account_id).get("parameters")

        always_merger.merge(result, manifest_parameters)
        always_merger.merge(result, launch_parameters)
        always_merger.merge(result, account_parameters)

        for p_name, p_details in result.items():
            if p_details.get("ssm"):
                for v_name, v_details in p_details.get("ssm").items():
                    result[p_name]["ssm"][v_name] = (
                        result[p_name]["ssm"][v_name]
                        .replace("${AWS::AccountId}", self.account_id)
                        .replace("${AWS::Region}", self.region)
                    )

        return result

    def get_parameter_values(self):
        all_params = {}
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

                parameter_task_output = self.get_output_from_reference_dependency(
                    required_task_reference
                )

                if parameter_task_output.get(requested_param_name):
                    all_params[param_name] = parameter_task_output.get(
                        requested_param_name,
                    ).get("Value")
                elif requested_param_details.get("default"):
                    all_params[param_name] = requested_param_details.get("default")
                else:
                    raise Exception(
                        f"Could not find parameter value and no default was set for {requested_param_name}"
                    )

            if param_details.get("boto3"):
                requested_param_details = param_details.get("boto3")
                boto3_task_account_id = requested_param_details.get("account_id")
                boto3_task_region = requested_param_details.get("region")
                if param_details.get("cloudformation_stack_output"):
                    task_ref = (
                        f"{constants.BOTO3_PARAMETERS}"
                        f"-cloudformation_stack_output"
                        f"-{param_details.get('cloudformation_stack_output').get('stack_name')}"
                        f"-{param_details.get('cloudformation_stack_output').get('output_key')}"
                        f"-{boto3_task_account_id}"
                        f"-{boto3_task_region}"
                    )

                elif param_details.get("servicecatalog_provisioned_product_output"):
                    task_ref = (
                        f"{constants.BOTO3_PARAMETERS}"
                        f"-servicecatalog_provisioned_product_output"
                        f"-{param_details.get('servicecatalog_provisioned_product_output').get('provisioned_product_name')}"
                        f"-{param_details.get('servicecatalog_provisioned_product_output').get('output_key')}"
                        f"-{boto3_task_account_id}"
                        f"-{boto3_task_region}"
                    )
                else:
                    task_ref = (
                        f"{constants.BOTO3_PARAMETERS}"
                        f"-{self.section_name}"
                        f"-{self.item_name}"
                        f"-{param_name}"
                        f"-{account_id_to_use_for_boto3_call}"
                        f"-{region_to_use_for_boto3_call}"
                    )

                task_ref = (
                    task_ref.replace("${AWS::AccountId}", self.account_id)
                    .replace("${AWS::PuppetAccountId}", self.puppet_account_id)
                    .replace("${AWS::Region}", self.region)
                )
                print(
                    f"Getting output for task: {task_ref} within task {self.task_reference}"
                )
                parameter_task_output = self.get_output_from_reference_dependency(
                    task_ref
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
                manifest = manifest_utils.Manifest(serialisation_utils.load(content))

                all_params[param_name] = manifest.get_mapping(
                    param_details.get("mapping"), self.account_id, self.region
                )
        return all_params
