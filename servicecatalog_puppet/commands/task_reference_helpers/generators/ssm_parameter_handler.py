#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants, task_reference_constants


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
    all_tasks, home_region, new_tasks, parameter_details, puppet_account_id, task
):
    if parameter_details.get("ssm"):
        ssm_parameter_details = parameter_details.get("ssm")
        task_account_id = task.get("account_id")
        task_region = task.get("region")
        parameter_account_id = (
            ssm_parameter_details.get("account_id", puppet_account_id)
            .replace("${AWS::AccountId}", task_account_id)
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )
        parameter_region = ssm_parameter_details.get("region", home_region).replace(
            "${AWS::Region}", task_region
        )
        ssm_parameter_partial_task_reference = (
            f"{parameter_account_id}-{parameter_region}"
        )
        parameter_name = (
            ssm_parameter_details.get("name")
            .replace("${AWS::Region}", task_region)
            .replace("${AWS::AccountId}", task_account_id)
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )

        path = ssm_parameter_details.get("path")
        if path is None:
            parameter_task_reference = f"{constants.SSM_PARAMETERS}-{ssm_parameter_partial_task_reference}-{parameter_name}"
        else:
            parameter_task_reference = f"{constants.SSM_PARAMETERS_WITH_A_PATH}-{ssm_parameter_partial_task_reference}-{path}"

        if all_tasks.get(parameter_task_reference):
            ssm_task_params = all_tasks.get(parameter_task_reference)
        else:
            if parameter_account_id not in [task_account_id, puppet_account_id]:
                raise Exception(
                    f"SSM Parameters can only come from the target account or the puppet account. "
                    + f"{task.get('task_reference')} in {task_account_id} is using {parameter_name} from {parameter_account_id}, "
                    + f"which is not the puppet_account_id {puppet_account_id}"
                )

            parameter_task_execution = task.get(
                "execution", constants.EXECUTION_MODE_DEFAULT
            )

            if (
                parameter_account_id != task_account_id
                and parameter_task_execution == constants.EXECUTION_MODE_SPOKE
            ):
                parameter_task_execution = constants.EXECUTION_MODE_HUB

            ssm_task_params = {
                "task_reference": parameter_task_reference,
                "account_id": parameter_account_id,
                "region": parameter_region,
                task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
                task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
                task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
                "dependencies": [],
                "dependencies_by_reference": [],
                "execution": parameter_task_execution,
            }

            if path is None:
                ssm_task_params["param_name"] = parameter_name
                ssm_task_params["section_name"] = constants.SSM_PARAMETERS
            else:
                ssm_task_params["path"] = path
                ssm_task_params["section_name"] = constants.SSM_PARAMETERS_WITH_A_PATH

            new_tasks[parameter_task_reference] = ssm_task_params

        ssm_task_params[task_reference_constants.MANIFEST_SECTION_NAMES].update(
            **task.get(task_reference_constants.MANIFEST_SECTION_NAMES)
        )
        ssm_task_params[task_reference_constants.MANIFEST_ITEM_NAMES].update(
            **task.get(task_reference_constants.MANIFEST_ITEM_NAMES)
        )
        ssm_task_params[task_reference_constants.MANIFEST_ACCOUNT_IDS].update(
            **task.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
        )

        task["dependencies_by_reference"].append(parameter_task_reference)

        if not task.get("ssm_parameters_tasks_references"):
            task["ssm_parameters_tasks_references"] = dict()

        task["ssm_parameters_tasks_references"][
            parameter_name
        ] = parameter_task_reference
