#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants, task_reference_constants


def ssm_outputs_handler(
    all_tasks,
    all_tasks_task_reference,
    home_region,
    item_name,
    puppet_account_id,
    section_name,
    task_to_add,
):
    for ssm_parameter_output in task_to_add.get("ssm_param_outputs", []):
        task_account_id = task_to_add.get("account_id")
        task_region = task_to_add.get("region")

        output_region = ssm_parameter_output.get("region", home_region).replace(
            "${AWS::Region}", task_region
        )
        output_account_id = (
            ssm_parameter_output.get("account_id", puppet_account_id)
            .replace("${AWS::AccountId}", task_account_id)
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )

        output_parameter_name = (
            ssm_parameter_output.get("param_name")
            .replace("${AWS::Region}", task_region)
            .replace("${AWS::AccountId}", task_account_id)
        )

        ssm_parameter_output_task_reference = f"{constants.SSM_OUTPUTS}-{output_account_id}-{output_region}-{output_parameter_name}"

        if all_tasks.get(ssm_parameter_output_task_reference):
            raise Exception(
                f"You have two tasks outputting the same SSM parameter output: {ssm_parameter_output.get('param_name')}: {ssm_parameter_output_task_reference}"
            )

        all_tasks[ssm_parameter_output_task_reference] = {
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            "task_reference": ssm_parameter_output_task_reference,
            "param_name": output_parameter_name,
            "stack_output": ssm_parameter_output.get("stack_output"),
            "force_operation": ssm_parameter_output.get("force_operation", False),
            "account_id": output_account_id,
            "region": output_region,
            "dependencies_by_reference": [all_tasks_task_reference],
            "task_generating_output": all_tasks_task_reference,
            "status": task_to_add.get("status"),
            "section_name": constants.SSM_OUTPUTS,
            "execution": task_to_add.get("execution", constants.EXECUTION_MODE_DEFAULT),
        }
        all_tasks[ssm_parameter_output_task_reference][
            task_reference_constants.MANIFEST_SECTION_NAMES
        ][section_name] = True
        all_tasks[ssm_parameter_output_task_reference][
            task_reference_constants.MANIFEST_ITEM_NAMES
        ][item_name] = True
        all_tasks[ssm_parameter_output_task_reference][
            task_reference_constants.MANIFEST_ACCOUNT_IDS
        ][output_account_id] = True

        if not task_to_add.get("ssm_outputs_tasks_references"):
            task_to_add["ssm_outputs_tasks_references"] = dict()

        task_to_add["ssm_outputs_tasks_references"][
            output_parameter_name
        ] = ssm_parameter_output_task_reference
