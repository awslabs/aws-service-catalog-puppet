#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants
from servicecatalog_puppet import yaml_utils


def get_dependencies_for_task_reference(
    manifest_task_reference_file_path, task_reference, puppet_account_id
):
    dependencies = dict()
    reference = yaml_utils.load(
        open(manifest_task_reference_file_path, "r").read()
    ).get("all_tasks")
    this_task = reference.get(task_reference)
    for dependency_by_reference in this_task.get("dependencies_by_reference", []):
        dependency_by_reference_params = reference.get(dependency_by_reference)
        t_reference = dependency_by_reference_params.get("task_reference")
        dependencies[t_reference] = create(
            manifest_task_reference_file_path,
            puppet_account_id,
            dependency_by_reference_params,
        )
    return dependencies


def create(
    manifest_task_reference_file_path, puppet_account_id, parameters_to_use,
):
    section_name = parameters_to_use.get("section_name")
    common_parameters = dict(
        puppet_account_id=puppet_account_id,
        task_reference=parameters_to_use.get("task_reference"),
        manifest_task_reference_file_path=manifest_task_reference_file_path,
        dependencies_by_reference=parameters_to_use.get("dependencies_by_reference"),
        account_id=parameters_to_use.get("account_id"),
        region=parameters_to_use.get("region"),
    )

    if section_name == constants.STACKS:
        from servicecatalog_puppet.workflow.stack.provision_stack_task import (
            ProvisionStackTask,
        )
        from servicecatalog_puppet.workflow.stack.terminate_stack_task import (
            TerminateStackTask,
        )

        if parameters_to_use.get("status") == "terminated":
            return TerminateStackTask(
                **common_parameters,
                stack_name=parameters_to_use.get("stack_name"),
                bucket=parameters_to_use.get("bucket"),
                key=parameters_to_use.get("key"),
                version_id=parameters_to_use.get("version_id"),
                launch_name=parameters_to_use.get("launch_name"),
                stack_set_name=parameters_to_use.get("stack_set_name"),
                capabilities=parameters_to_use.get("capabilities"),
                ssm_param_inputs=[],
                launch_parameters=parameters_to_use.get("launch_parameters"),
                manifest_parameters=parameters_to_use.get(""),
                account_parameters=parameters_to_use.get(""),
                retry_count=parameters_to_use.get("retry_count"),
                worker_timeout=parameters_to_use.get("worker_timeout"),
                ssm_param_outputs=[],
                requested_priority=parameters_to_use.get("requested_priority"),
                use_service_role=parameters_to_use.get("use_service_role"),
                execution=parameters_to_use.get("execution"),
                manifest_file_path="ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml",  # TODO move to params
            )
        else:
            return ProvisionStackTask(
                **common_parameters,
                stack_name=parameters_to_use.get("stack_name"),
                bucket=parameters_to_use.get("bucket"),
                key=parameters_to_use.get("key"),
                version_id=parameters_to_use.get("version_id"),
                launch_name=parameters_to_use.get("launch_name"),
                stack_set_name=parameters_to_use.get("stack_set_name"),
                capabilities=parameters_to_use.get("capabilities"),
                ssm_param_inputs=[],
                launch_parameters=parameters_to_use.get("launch_parameters"),
                manifest_parameters=parameters_to_use.get(""),
                account_parameters=parameters_to_use.get(""),
                retry_count=parameters_to_use.get("retry_count"),
                worker_timeout=parameters_to_use.get("worker_timeout"),
                ssm_param_outputs=[],
                requested_priority=parameters_to_use.get("requested_priority"),
                use_service_role=parameters_to_use.get("use_service_role"),
                execution=parameters_to_use.get("execution"),
                manifest_file_path="ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml",  # TODO move to params
            )
    elif section_name == constants.SSM_PARAMETERS:
        from servicecatalog_puppet.workflow.ssm import get_ssm_parameter_task

        return get_ssm_parameter_task.GetSSMParameterTask(
            **common_parameters, param_name=parameters_to_use.get("param_name"),
        )
    elif section_name == constants.SSM_OUTPUTS:
        from servicecatalog_puppet.workflow.ssm import ssm_outputs_task

        return ssm_outputs_task.SSMOutputsTasks(
            **common_parameters,
            param_name=parameters_to_use.get("param_name"),
            stack_output=parameters_to_use.get("stack_output"),
            task_generating_output=parameters_to_use.get("task_generating_output"),
            force_operation=parameters_to_use.get("force_operation"),
        )
