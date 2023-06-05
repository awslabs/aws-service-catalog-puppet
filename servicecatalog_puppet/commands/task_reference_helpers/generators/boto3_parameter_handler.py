#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants


def boto3_parameter_handler(
    new_tasks, parameter_details, parameter_name, puppet_account_id, task
):
    if parameter_details.get("boto3"):
        boto3_parameter_details = parameter_details.get("boto3")
        account_id_to_use_for_boto3_call = (
            str(boto3_parameter_details.get("account_id", puppet_account_id))
            .replace("${AWS::AccountId}", task.get("account_id"))
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )
        region_to_use_for_boto3_call = boto3_parameter_details.get(
            "region", constants.HOME_REGION
        ).replace("${AWS::Region}", task.get("region"))

        boto3_parameter_task_reference = (
            f"{constants.BOTO3_PARAMETERS}"
            f"-{task.get('section_name')}"
            f"-{task.get('item_name')}"
            f"-{parameter_name}"
            f"-{account_id_to_use_for_boto3_call}"
            f"-{region_to_use_for_boto3_call}"
        )
        task_execution = task.get("execution", constants.EXECUTION_MODE_DEFAULT)
        if task.get(task_execution) in [
            constants.EXECUTION_MODE_HUB,
            constants.EXECUTION_MODE_ASYNC,
        ]:
            if account_id_to_use_for_boto3_call != puppet_account_id:
                raise Exception(
                    f"Cannot use cross account Boto3 Parameters in execution mode: {task_execution}"
                )
        if not new_tasks.get(boto3_parameter_task_reference):
            new_tasks[boto3_parameter_task_reference] = dict(
                status=task.get("status"),
                execution=task_execution,
                task_reference=boto3_parameter_task_reference,
                dependencies_by_reference=[],
                dependencies=[],
                manifest_section_names=dict(),
                manifest_item_names=dict(),
                manifest_account_ids=dict(),
                account_id=account_id_to_use_for_boto3_call,
                region=region_to_use_for_boto3_call,
                arguments=boto3_parameter_details.get("arguments"),
                call=boto3_parameter_details.get("call"),
                client=boto3_parameter_details.get("client"),
                filter=boto3_parameter_details.get("filter"),
                use_paginator=boto3_parameter_details.get("use_paginator"),
                section_name=constants.BOTO3_PARAMETERS,
            )

        boto3_task = new_tasks[boto3_parameter_task_reference]
        boto3_task["manifest_section_names"].update(task.get("manifest_section_names"))
        boto3_task["manifest_item_names"].update(task.get("manifest_item_names"))
        boto3_task["manifest_account_ids"].update(task.get("manifest_account_ids"))
        boto3_task["dependencies"].extend(task.get("dependencies"))

        task["dependencies_by_reference"].append(boto3_parameter_task_reference)
