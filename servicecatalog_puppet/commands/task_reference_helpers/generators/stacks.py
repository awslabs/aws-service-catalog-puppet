#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants, task_reference_constants


def handle_stacks(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    prepare_task_reference = (
        f"{constants.PREPARE_ACCOUNT_FOR_STACKS}-{task_to_add.get('account_id')}"
    )
    if not all_tasks.get(prepare_task_reference):
        all_tasks[prepare_task_reference] = {
            "task_reference": prepare_task_reference,
            "account_id": task_to_add.get("account_id"),
            "region": constants.HOME_REGION,
            "puppet_account_id": puppet_account_id,
            "dependencies_by_reference": [constants.CREATE_POLICIES],
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            "section_name": constants.PREPARE_ACCOUNT_FOR_STACKS,
        }
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        prepare_task_reference
    )
    all_tasks[prepare_task_reference][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[prepare_task_reference][
        task_reference_constants.MANIFEST_ITEM_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES))
    all_tasks[prepare_task_reference][
        task_reference_constants.MANIFEST_ACCOUNT_IDS
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))

    get_s3_template_ref = f"{constants.GET_TEMPLATE_FROM_S3}-{section_name}-{item_name}"
    if not all_tasks.get(get_s3_template_ref):
        all_tasks[get_s3_template_ref] = {
            "task_reference": get_s3_template_ref,
            "execution": "hub",
            "bucket": task_to_add.get("bucket"),
            "key": task_to_add.get("key"),
            "region": task_to_add.get("region"),
            "version_id": task_to_add.get("version_id"),
            "puppet_account_id": puppet_account_id,
            "account_id": puppet_account_id,
            "dependencies_by_reference": [constants.CREATE_POLICIES],
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            "section_name": constants.GET_TEMPLATE_FROM_S3,
        }
    all_tasks[all_tasks_task_reference]["get_s3_template_ref"] = get_s3_template_ref
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        get_s3_template_ref
    )
    all_tasks[get_s3_template_ref][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[get_s3_template_ref][task_reference_constants.MANIFEST_ITEM_NAMES].update(
        task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES)
    )
    all_tasks[get_s3_template_ref][
        task_reference_constants.MANIFEST_ACCOUNT_IDS
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))
