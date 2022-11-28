#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants


def handle_workspaces(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    workspace_account_preparation_ref = (
        f"{constants.WORKSPACE_ACCOUNT_PREPARATION}-{task_to_add.get('account_id')}"
    )
    if all_tasks.get(workspace_account_preparation_ref) is None:
        all_tasks[workspace_account_preparation_ref] = dict(
            puppet_account_id=puppet_account_id,
            task_reference=workspace_account_preparation_ref,
            dependencies_by_reference=[constants.CREATE_POLICIES],
            account_id=task_to_add.get("account_id"),
            section_name=constants.WORKSPACE_ACCOUNT_PREPARATION,
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
        )
    all_tasks[workspace_account_preparation_ref]["manifest_section_names"].update(
        task_to_add.get("manifest_section_names")
    )
    all_tasks[workspace_account_preparation_ref]["manifest_item_names"].update(
        task_to_add.get("manifest_item_names")
    )
    all_tasks[workspace_account_preparation_ref]["manifest_account_ids"].update(
        task_to_add.get("manifest_account_ids")
    )
    if workspace_account_preparation_ref not in all_tasks[all_tasks_task_reference].get(
        "dependencies_by_reference"
    ):
        all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
            workspace_account_preparation_ref
        )
