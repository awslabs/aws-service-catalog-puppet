#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import copy
import os

from servicecatalog_puppet import constants


def handle_organizational_units(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    if not task_to_add.get("parent_ou_id"):
        # parent may not exist as it wasn't specified
        parent_path = os.path.dirname(task_to_add.get("path"))
        if parent_path != task_to_add.get("path"):
            parent_task_reference = f"{constants.ORGANIZATIONAL_UNITS}_{parent_path.replace('/', '%2F')}_{task_to_add.get('account_id')}_{task_to_add.get('region')}"
            if not all_tasks.get(parent_task_reference):
                parent_task_to_add = copy.deepcopy(task_to_add)
                parent_task_to_add["task_reference"] = parent_task_reference
                parent_task_to_add["path"] = parent_path
                if parent_path == "/":
                    parent_task_to_add["name"] = parent_path
                else:
                    parent_task_to_add["name"] = os.path.basename(parent_path)
                all_tasks[parent_task_reference] = parent_task_to_add
                handle_organizational_units(
                    all_tasks,
                    all_tasks_task_reference,
                    item_name,
                    puppet_account_id,
                    section_name,
                    parent_task_reference,
                    parent_task_to_add,
                )
            task_to_add["parent_ou_task_ref"] = parent_task_reference
            task_to_add["dependencies_by_reference"].append(parent_task_reference)
