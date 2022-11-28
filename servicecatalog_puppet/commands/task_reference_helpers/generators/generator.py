#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants
from servicecatalog_puppet.commands.task_reference_helpers.generators import (
    launches,
    spoke_local_portfolios,
    workspaces,
    stacks,
    service_control_policies,
    tag_policies,
    organizational_units,
)


def generate(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):

    if section_name == constants.LAUNCHES:
        launches.handle_launches(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )

    if section_name == constants.SPOKE_LOCAL_PORTFOLIOS:
        spoke_local_portfolios.handle_spoke_local_portfolios(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )

    if section_name == constants.WORKSPACES:
        workspaces.handle_workspaces(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )

    if section_name == constants.STACKS:
        stacks.handle_stacks(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )

    if section_name == constants.SERVICE_CONTROL_POLICIES:
        service_control_policies.handle_service_control_policies(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )

    if section_name == constants.TAG_POLICIES:
        tag_policies.handle_tag_policies(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )

    if section_name == constants.ORGANIZATIONAL_UNITS:
        organizational_units.handle_organizational_units(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
        )
