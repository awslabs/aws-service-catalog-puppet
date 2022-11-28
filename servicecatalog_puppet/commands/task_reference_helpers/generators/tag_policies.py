#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants


def handle_tag_policies(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    get_or_create_policy_ref = (
        f"{constants.GET_OR_CREATE_TAG_POLICIES_POLICY}-{item_name}"
    )
    if not all_tasks.get(get_or_create_policy_ref):
        all_tasks[get_or_create_policy_ref] = dict(
            task_reference=get_or_create_policy_ref,
            execution="hub",
            account_id=puppet_account_id,
            region=task_to_add.get("region"),
            policy_name=task_to_add.get("tag_policy_name"),
            policy_description=task_to_add.get("description"),
            policy_content=task_to_add.get("content"),
            dependencies_by_reference=list(),
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
            section_name=constants.GET_OR_CREATE_TAG_POLICIES_POLICY,
        )
        all_tasks[all_tasks_task_reference][
            "get_or_create_policy_ref"
        ] = get_or_create_policy_ref
        all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
            get_or_create_policy_ref
        )
        all_tasks[get_or_create_policy_ref]["manifest_section_names"].update(
            task_to_add.get("manifest_section_names")
        )
        all_tasks[get_or_create_policy_ref]["manifest_item_names"].update(
            task_to_add.get("manifest_item_names")
        )
        all_tasks[get_or_create_policy_ref]["manifest_account_ids"].update(
            task_to_add.get("manifest_account_ids")
        )
