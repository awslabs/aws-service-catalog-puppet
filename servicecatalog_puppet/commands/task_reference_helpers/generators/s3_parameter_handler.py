#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants, task_reference_constants


def s3_parameter_handler(
    all_tasks, home_region, new_tasks, parameter_details, puppet_account_id, task
):
    if parameter_details.get("s3"):
        s3_parameter_details = parameter_details.get("s3")
        key = str(s3_parameter_details.get("key"))
        jmespath = str(s3_parameter_details.get("jmespath"))
        default = str(s3_parameter_details.get("default"))

        task_account_id = task.get("account_id")
        task_region = task.get("region")

        key = (
            key.replace("${AWS::Region}", task_region)
            .replace("${AWS::AccountId}", task_account_id)
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )
        jmespath = (
            jmespath.replace("${AWS::Region}", task_region)
            .replace("${AWS::AccountId}", task_account_id)
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )
        default = (
            default.replace("${AWS::Region}", task_region)
            .replace("${AWS::AccountId}", task_account_id)
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )

        s3_object_task_reference = f"{constants.S3_GET_OBJECT}-{key}"

        if not all_tasks.get(s3_object_task_reference):
            new_tasks[s3_object_task_reference] = {
                "task_reference": s3_object_task_reference,
                "account_id": puppet_account_id,
                "region": home_region,
                "key": key,
                task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
                task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
                task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
                "dependencies": [],
                "dependencies_by_reference": [],
                "execution": constants.EXECUTION_MODE_HUB,
                "section_name": constants.S3_GET_OBJECT,
            }

        new_tasks[s3_object_task_reference][
            task_reference_constants.MANIFEST_SECTION_NAMES
        ].update(**task.get(task_reference_constants.MANIFEST_SECTION_NAMES))
        new_tasks[s3_object_task_reference][
            task_reference_constants.MANIFEST_ITEM_NAMES
        ].update(**task.get(task_reference_constants.MANIFEST_ITEM_NAMES))
        new_tasks[s3_object_task_reference][
            task_reference_constants.MANIFEST_ACCOUNT_IDS
        ].update(**task.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))

        task["dependencies_by_reference"].append(s3_object_task_reference)

        if not task.get("s3_object_task_reference"):
            task["s3_object_task_reference"] = dict()

        parameter_name = (
            str(s3_parameter_details.get("name"))
            .replace("${AWS::Region}", task_region)
            .replace("${AWS::AccountId}", task_account_id)
            .replace("${AWS::PuppetAccountId}", puppet_account_id)
        )

        task["s3_object_task_reference"][parameter_name] = s3_object_task_reference
