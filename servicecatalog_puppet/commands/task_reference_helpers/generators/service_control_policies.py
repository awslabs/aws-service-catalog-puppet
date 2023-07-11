#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants, task_reference_constants


def handle_service_control_policies(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    get_or_create_policy_ref = (
        f"{constants.GET_OR_CREATE_SERVICE_CONTROL_POLICIES_POLICY}-{item_name}"
    )
    if not all_tasks.get(get_or_create_policy_ref):
        all_tasks[get_or_create_policy_ref] = {
            "task_reference": get_or_create_policy_ref,
            "execution": "hub",
            "account_id": puppet_account_id,
            "region": task_to_add.get("region"),
            "policy_name": task_to_add.get("service_control_policy_name"),
            "policy_description": task_to_add.get("description"),
            "policy_content": task_to_add.get("content"),
            "dependencies_by_reference": list(),
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            "section_name": constants.GET_OR_CREATE_SERVICE_CONTROL_POLICIES_POLICY,
        }
    all_tasks[all_tasks_task_reference][
        "get_or_create_policy_ref"
    ] = get_or_create_policy_ref
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        get_or_create_policy_ref
    )
    all_tasks[get_or_create_policy_ref][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[get_or_create_policy_ref][
        task_reference_constants.MANIFEST_ITEM_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES))
    all_tasks[get_or_create_policy_ref][
        task_reference_constants.MANIFEST_ACCOUNT_IDS
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))
