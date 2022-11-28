#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants


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
        all_tasks[prepare_task_reference] = dict(
            task_reference=prepare_task_reference,
            account_id=task_to_add.get("account_id"),
            region=constants.HOME_REGION,
            puppet_account_id=puppet_account_id,
            dependencies_by_reference=[constants.CREATE_POLICIES],
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
            section_name=constants.PREPARE_ACCOUNT_FOR_STACKS,
        )
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        prepare_task_reference
    )
    all_tasks[prepare_task_reference]["manifest_section_names"].update(
        task_to_add.get("manifest_section_names")
    )
    all_tasks[prepare_task_reference]["manifest_item_names"].update(
        task_to_add.get("manifest_item_names")
    )
    all_tasks[prepare_task_reference]["manifest_account_ids"].update(
        task_to_add.get("manifest_account_ids")
    )

    get_s3_template_ref = f"{constants.GET_TEMPLATE_FROM_S3}-{section_name}-{item_name}"
    if not all_tasks.get(get_s3_template_ref):
        all_tasks[get_s3_template_ref] = dict(
            task_reference=get_s3_template_ref,
            execution="hub",
            bucket=task_to_add.get("bucket"),
            key=task_to_add.get("key"),
            region=task_to_add.get("region"),
            version_id=task_to_add.get("version_id"),
            puppet_account_id=puppet_account_id,
            account_id=puppet_account_id,
            dependencies_by_reference=[constants.CREATE_POLICIES],
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
            section_name=constants.GET_TEMPLATE_FROM_S3,
        )
    all_tasks[all_tasks_task_reference]["get_s3_template_ref"] = get_s3_template_ref
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        get_s3_template_ref
    )
    all_tasks[get_s3_template_ref]["manifest_section_names"].update(
        task_to_add.get("manifest_section_names")
    )
    all_tasks[get_s3_template_ref]["manifest_item_names"].update(
        task_to_add.get("manifest_item_names")
    )
    all_tasks[get_s3_template_ref]["manifest_account_ids"].update(
        task_to_add.get("manifest_account_ids")
    )
