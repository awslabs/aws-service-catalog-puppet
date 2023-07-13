#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants, task_reference_constants


def get_or_create_describe_portfolio_shares_task_ref(
    all_tasks, puppet_account_id, sharing_type, portfolio_task_ref, task_to_add
):
    describe_portfolio_shares_task_ref = (
        f"{constants.DESCRIBE_PORTFOLIO_SHARES}-{sharing_type}-{portfolio_task_ref}"
    )
    if not all_tasks.get(describe_portfolio_shares_task_ref):
        all_tasks[describe_portfolio_shares_task_ref] = {
            "section_name": constants.DESCRIBE_PORTFOLIO_SHARES,
            "task_reference": describe_portfolio_shares_task_ref,
            "account_id": puppet_account_id,
            "region": task_to_add.get("region"),
            "type": sharing_type,
            "portfolio_task_reference": portfolio_task_ref,
            "dependencies_by_reference": [portfolio_task_ref],
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
        }
    task = all_tasks[describe_portfolio_shares_task_ref]
    task[task_reference_constants.MANIFEST_SECTION_NAMES].update(
        task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES)
    )
    task[task_reference_constants.MANIFEST_ITEM_NAMES].update(
        task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES)
    )
    task[task_reference_constants.MANIFEST_ACCOUNT_IDS].update(
        task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
    )

    return describe_portfolio_shares_task_ref
