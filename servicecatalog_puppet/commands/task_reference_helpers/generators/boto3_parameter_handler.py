#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants, task_reference_constants


def generate_task_reference(
    parameter_details, account_id_to_use_for_boto3_call, region_to_use_for_boto3_call,
):
    if parameter_details.get("cloudformation_stack_output"):
        return (
            f"{constants.BOTO3_PARAMETERS}"
            f"-cloudformation_stack_output"
            f"-{parameter_details.get('cloudformation_stack_output').get('stack_name')}"
            f"-{parameter_details.get('cloudformation_stack_output').get('output_key')}"
            f"-{account_id_to_use_for_boto3_call}"
            f"-{region_to_use_for_boto3_call}"
        )
    elif parameter_details.get("servicecatalog_provisioned_product_output"):
        return (
            f"{constants.BOTO3_PARAMETERS}"
            f"-servicecatalog_provisioned_product_output"
            f"-{parameter_details.get('servicecatalog_provisioned_product_output').get('provisioned_product_name')}"
            f"-{parameter_details.get('servicecatalog_provisioned_product_output').get('output_key')}"
            f"-{account_id_to_use_for_boto3_call}"
            f"-{region_to_use_for_boto3_call}"
        )

    elif parameter_details.get("boto3"):
        return (
            f"{constants.BOTO3_PARAMETERS}"
            f"-{task.get('section_name')}"
            f"-{task.get('item_name')}"
            f"-{parameter_name}"
            f"-{account_id_to_use_for_boto3_call}"
            f"-{region_to_use_for_boto3_call}"
        )


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

        boto3_parameter_task_reference = generate_task_reference(
            parameter_details,
            account_id_to_use_for_boto3_call,
            region_to_use_for_boto3_call,
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
            new_tasks[boto3_parameter_task_reference] = {
                "status": task.get("status"),
                "execution": task_execution,
                "task_reference": boto3_parameter_task_reference,
                "dependencies_by_reference": [],
                "dependencies": [],
                task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
                task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
                task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
                "account_id": account_id_to_use_for_boto3_call,
                "region": region_to_use_for_boto3_call,
                "arguments": boto3_parameter_details.get("arguments"),
                "call": boto3_parameter_details.get("call"),
                "client": boto3_parameter_details.get("client"),
                "filter": boto3_parameter_details.get("filter"),
                "use_paginator": boto3_parameter_details.get("use_paginator"),
                "section_name": constants.BOTO3_PARAMETERS,
            }

        boto3_task = new_tasks[boto3_parameter_task_reference]
        boto3_task[task_reference_constants.MANIFEST_SECTION_NAMES].update(
            task.get(task_reference_constants.MANIFEST_SECTION_NAMES)
        )
        boto3_task[task_reference_constants.MANIFEST_ITEM_NAMES].update(
            task.get(task_reference_constants.MANIFEST_ITEM_NAMES)
        )
        boto3_task[task_reference_constants.MANIFEST_ACCOUNT_IDS].update(
            task.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
        )

        task["dependencies_by_reference"].append(boto3_parameter_task_reference)

        if not task.get("boto3_parameters_tasks_references"):
            task["boto3_parameters_tasks_references"] = dict()

        task["boto3_parameters_tasks_references"][
            parameter_name
        ] = boto3_parameter_task_reference
