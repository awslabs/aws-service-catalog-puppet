#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants
from servicecatalog_puppet.commands.task_reference_helpers.generators import (
    c7n_aws_lambdas,
    imported_portfolios,
    launches,
    organizational_units,
    service_control_policies,
    spoke_local_portfolios,
    stacks,
    tag_policies,
    workspaces,
)


def generate(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
    manifest,
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

    if section_name == constants.IMPORTED_PORTFOLIOS:
        imported_portfolios.handle_imported_portfolios(
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

    if section_name == constants.C7N_AWS_LAMBDAS:
        c7n_aws_lambdas.handle_c7n_aws_lambdas(
            all_tasks,
            all_tasks_task_reference,
            item_name,
            puppet_account_id,
            section_name,
            task_reference,
            task_to_add,
            manifest,
        )
