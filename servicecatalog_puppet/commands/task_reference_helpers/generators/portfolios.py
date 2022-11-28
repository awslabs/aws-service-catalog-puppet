#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants


def get_or_create_describe_portfolio_shares_task_ref(
    all_tasks, puppet_account_id, sharing_type, portfolio_task_ref, task_to_add
):
    describe_portfolio_shares_task_ref = (
        f"{constants.DESCRIBE_PORTFOLIO_SHARES}-{sharing_type}-{portfolio_task_ref}"
    )
    if not all_tasks.get(describe_portfolio_shares_task_ref):
        all_tasks[describe_portfolio_shares_task_ref] = dict(
            section_name=constants.DESCRIBE_PORTFOLIO_SHARES,
            task_reference=describe_portfolio_shares_task_ref,
            account_id=puppet_account_id,
            region=task_to_add.get("region"),
            type=sharing_type,
            portfolio_task_reference=portfolio_task_ref,
            dependencies_by_reference=[portfolio_task_ref],
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
        )
    task = all_tasks[describe_portfolio_shares_task_ref]
    task["manifest_section_names"].update(task_to_add.get("manifest_section_names"))
    task["manifest_item_names"].update(task_to_add.get("manifest_item_names"))
    task["manifest_account_ids"].update(task_to_add.get("manifest_account_ids"))

    return describe_portfolio_shares_task_ref
