#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants


def ssm_outputs_handler(
    all_tasks,
    all_tasks_task_reference,
    default_region,
    item_name,
    puppet_account_id,
    section_name,
    task_to_add,
):
    for ssm_parameter_output in task_to_add.get("ssm_param_outputs", []):
        output_region = ssm_parameter_output.get("region", default_region)
        task_account_id = task_to_add.get("account_id")
        output_account_id = ssm_parameter_output.get(
            "account_id", puppet_account_id
        ).replace("${AWS::AccountId}", task_account_id)
        ssm_parameter_output_task_reference = f'{constants.SSM_OUTPUTS}-{output_account_id}-{output_region}-{ssm_parameter_output.get("param_name")}'
        ssm_parameter_output_task_reference = ssm_parameter_output_task_reference.replace(
            "${AWS::Region}", task_to_add.get("region")
        ).replace(
            "${AWS::AccountId}", task_account_id
        )
        if all_tasks.get(ssm_parameter_output_task_reference):
            raise Exception(
                f"You have two tasks outputting the same SSM parameter output: {ssm_parameter_output.get('param_name')}: {ssm_parameter_output_task_reference}"
            )

        else:
            all_tasks[ssm_parameter_output_task_reference] = dict(
                manifest_section_names=dict(),
                manifest_item_names=dict(),
                manifest_account_ids=dict(),
                task_reference=ssm_parameter_output_task_reference,
                param_name=ssm_parameter_output.get("param_name")
                .replace("${AWS::Region}", task_to_add.get("region"))
                .replace("${AWS::AccountId}", task_account_id),
                stack_output=ssm_parameter_output.get("stack_output"),
                force_operation=ssm_parameter_output.get("force_operation", False),
                account_id=output_account_id,
                region=output_region,
                dependencies_by_reference=[all_tasks_task_reference],
                task_generating_output=all_tasks_task_reference,
                status=task_to_add.get("status"),
                section_name=constants.SSM_OUTPUTS,
                execution=task_to_add.get(
                    "execution", constants.EXECUTION_MODE_DEFAULT
                ),
            )
        all_tasks[ssm_parameter_output_task_reference]["manifest_section_names"][
            section_name
        ] = True
        all_tasks[ssm_parameter_output_task_reference]["manifest_item_names"][
            item_name
        ] = True
        all_tasks[ssm_parameter_output_task_reference]["manifest_account_ids"][
            output_account_id
        ] = True
