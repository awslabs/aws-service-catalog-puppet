#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants


def assertCrossAccountAccessWillWork(
    owning_account, task, task_execution, puppet_account_id
):
    if task_execution not in [
        constants.EXECUTION_MODE_HUB,
        constants.EXECUTION_MODE_ASYNC,
    ]:
        if (
            owning_account != task.get("account_id")
            and owning_account != puppet_account_id
        ):
            message = f"Cannot use cross account SSM parameters in execution mode: {task_execution}."
            message += f"For task {task.get('task_reference')}, "
            message += f"parameter is in account {owning_account} and task will execute in {task.get('account_id')}."
            raise Exception(message)


def ssm_parameter_handler(
    all_tasks, default_region, new_tasks, parameter_details, puppet_account_id, task
):
    if parameter_details.get("ssm"):
        ssm_parameter_details = parameter_details.get("ssm")
        interpolation_output_account = task.get("account_id")
        interpolation_output_region = task.get("region")
        owning_account = ssm_parameter_details.get(
            "account_id", puppet_account_id
        ).replace("${AWS::AccountId}", interpolation_output_account)
        owning_region = ssm_parameter_details.get("region", default_region).replace(
            "${AWS::Region}", interpolation_output_region
        )
        task_reference = f"{owning_account}-{owning_region}"
        param_name = (
            ssm_parameter_details.get("name")
            .replace("${AWS::Region}", interpolation_output_region)
            .replace("${AWS::AccountId}", interpolation_output_account)
        )

        task_execution = task.get("execution", constants.EXECUTION_MODE_DEFAULT)
        if owning_account == puppet_account_id:
            task_execution = constants.EXECUTION_MODE_HUB
        assertCrossAccountAccessWillWork(
            owning_account, task, task_execution, puppet_account_id
        )

        if task.get(task_execution) in [
            constants.EXECUTION_MODE_HUB,
            constants.EXECUTION_MODE_ASYNC,
        ]:
            if owning_account != puppet_account_id:
                raise Exception(
                    f"Cannot use cross account SSM parameters in execution mode: {task_execution}"
                )

        task_def = dict(
            account_id=owning_account,
            region=owning_region,
            manifest_section_names=dict(**task.get("manifest_section_names")),
            manifest_item_names=dict(**task.get("manifest_item_names")),
            manifest_account_ids=dict(**task.get("manifest_account_ids")),
            dependencies=[],
            execution=task_execution,
        )
        path = ssm_parameter_details.get("path")
        if path is None:
            ssm_parameter_task_reference = (
                f"{constants.SSM_PARAMETERS}-{task_reference}-{param_name}"
            )
            task_def["param_name"] = param_name
            task_def["section_name"] = constants.SSM_PARAMETERS
        else:
            ssm_parameter_task_reference = (
                f"{constants.SSM_PARAMETERS_WITH_A_PATH}-{task_reference}-{path}"
            )
            task_def["path"] = path
            task_def["section_name"] = constants.SSM_PARAMETERS_WITH_A_PATH
        task_def["task_reference"] = ssm_parameter_task_reference

        potential_output_task_ref = f"{constants.SSM_PARAMETERS}-{task_reference}-{param_name}".replace(
            f"{constants.SSM_PARAMETERS}-", f"{constants.SSM_OUTPUTS}-"
        )
        if all_tasks.get(potential_output_task_ref):
            dependency = [potential_output_task_ref]
        else:
            dependency = []
        task_def["dependencies_by_reference"] = dependency

        # IF THERE ARE TWO TASKS USING THE SAME PARAMETER AND THE OTHER TASK ADDED IT FIRST
        if new_tasks.get(ssm_parameter_task_reference):
            existing_task_def = new_tasks[ssm_parameter_task_reference]
            # AVOID DUPLICATE DEPENDENCIES IN THE SAME LIST
            for dep in dependency:
                if dep not in existing_task_def["dependencies_by_reference"]:
                    existing_task_def["dependencies_by_reference"].append(dep)
        else:
            new_tasks[ssm_parameter_task_reference] = task_def

        ssm_parameter_task = new_tasks[ssm_parameter_task_reference]
        ssm_parameter_task["manifest_section_names"].update(
            task.get("manifest_section_names")
        )
        ssm_parameter_task["manifest_item_names"].update(
            task.get("manifest_item_names")
        )
        ssm_parameter_task["manifest_account_ids"].update(
            task.get("manifest_account_ids")
        )
        ssm_parameter_task["dependencies"].extend(task.get("dependencies"))

        task["dependencies_by_reference"].append(ssm_parameter_task_reference)
