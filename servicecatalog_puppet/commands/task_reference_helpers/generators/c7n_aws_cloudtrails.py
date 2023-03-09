#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants


def manifest_related_args(task_to_add):
    return dict(
        manifest_section_names=dict(**task_to_add.get("manifest_section_names")),
        manifest_item_names=dict(**task_to_add.get("manifest_item_names")),
        manifest_account_ids=dict(**task_to_add.get("manifest_account_ids")),
    )


def create_custodian_role(
    task_to_add,
    all_tasks,
    account_id,
    custodian_account_id,
    custodian_region,
    custodian_role_name,
    custodian_role_path,
    custodian_role_managed_policy_arns,
):
    create_custodian_role_ref = (
        f"{constants.C7N_CREATE_CUSTODIAN_ROLE_TASK}-{account_id}"
    )
    all_tasks[create_custodian_role_ref] = dict(
        section_name=constants.C7N_CREATE_CUSTODIAN_ROLE_TASK,
        task_reference=create_custodian_role_ref,
        account_id=account_id,
        region=custodian_region,
        c7n_account_id=custodian_account_id,
        role_name=custodian_role_name,
        role_path=custodian_role_path,
        role_managed_policy_arns=custodian_role_managed_policy_arns,
        dependencies_by_reference=[],
        execution=task_to_add.get("execution"),
        **manifest_related_args(task_to_add),
    )


def prepare_account_as_hub(
    task_to_add,
    all_tasks,
    custodian_account_id,
    custodian_region,
    custodian_role_name,
    custodian_role_path,
    custodian_c7n_version,
    organization,
):
    create_custodian_event_bus_task_ref = (
        f"{constants.C7N_PREPARE_HUB_ACCOUNT_TASK}-{custodian_account_id}"
    )
    all_tasks[create_custodian_event_bus_task_ref] = dict(
        task_reference=create_custodian_event_bus_task_ref,
        section_name=constants.C7N_PREPARE_HUB_ACCOUNT_TASK,
        account_id=custodian_account_id,
        region=custodian_region,
        custodian_region=custodian_region,
        c7n_version=custodian_c7n_version,
        organization=organization,
        role_name=custodian_role_name,
        role_path=custodian_role_path,
        dependencies_by_reference=[],
        execution=task_to_add.get("execution"),
        **manifest_related_args(task_to_add),
    )


def forward_events_account_task(
    task_to_add, all_tasks, account_id, custodian_account_id, custodian_region
):
    forward_events_for_account_tasks = (
        f"{constants.C7N_FORWARD_EVENTS_FOR_ACCOUNT_TASK}-{account_id}"
    )
    all_tasks[forward_events_for_account_tasks] = dict(
        section_name=constants.C7N_FORWARD_EVENTS_FOR_ACCOUNT_TASK,
        task_reference=forward_events_for_account_tasks,
        account_id=account_id,
        region=custodian_region,
        c7n_account_id=custodian_account_id,
        custodian_region=custodian_region,
        dependencies_by_reference=[
            f"{constants.C7N_PREPARE_HUB_ACCOUNT_TASK}-{custodian_account_id}",
        ],
        execution=task_to_add.get("execution"),
        **manifest_related_args(task_to_add),
    )


def forward_events_region_task(
    task_to_add, all_tasks, account_id, region, custodian_account_id, custodian_region
):
    if account_id == custodian_account_id and region == custodian_region:
        return

    forward_events_for_region_task = (
        f"{constants.C7N_FORWARD_EVENTS_FOR_REGION_TASK}-{account_id}-{region}"
    )
    all_tasks[forward_events_for_region_task] = dict(
        section_name=constants.C7N_FORWARD_EVENTS_FOR_REGION_TASK,
        task_reference=forward_events_for_region_task,
        account_id=account_id,
        region=region,
        c7n_account_id=custodian_account_id,
        custodian_region=custodian_region,
        dependencies_by_reference=[
            f"{constants.C7N_FORWARD_EVENTS_FOR_ACCOUNT_TASK}-{account_id}",
        ],
        execution=task_to_add.get("execution"),
        **manifest_related_args(task_to_add),
    )


def deploy_policies(
    task_to_add,
    all_tasks,
    account_id,
    region,
    custodian_account_id,
    custodian_region,
    role_name,
    role_path,
):
    deploy_policies_task_ref = (
        f"{constants.C7N_DEPLOY_POLICIES_TASK}-{custodian_account_id}"
    )
    if all_tasks.get(deploy_policies_task_ref) is None:
        all_tasks[deploy_policies_task_ref] = dict(
            section_name=constants.C7N_DEPLOY_POLICIES_TASK,
            task_reference=deploy_policies_task_ref,
            account_id=custodian_account_id,
            region=custodian_region,
            policies=task_to_add.get("policies"),
            deployments=dict(),
            role_name=role_name,
            role_path=role_path,
            dependencies_by_reference=[
                # custodian dependencies
                f"{constants.C7N_CREATE_CUSTODIAN_ROLE_TASK}-{custodian_account_id}",
                f"{constants.C7N_PREPARE_HUB_ACCOUNT_TASK}-{custodian_account_id}",
            ],
            execution=task_to_add.get("execution"),
            **manifest_related_args(task_to_add),
        )
    deploy_policies_task = all_tasks[deploy_policies_task_ref]
    if deploy_policies_task["deployments"].get(region) is None:
        deploy_policies_task["deployments"][region] = list()
    deploy_policies_task["deployments"][region].append(account_id)


def handle_c7n_aws_cloudtrails_for_custodian(
    task_to_add,
    all_tasks,
    region,
    custodian_account_id,
    custodian_region,
    custodian_role_name,
    custodian_role_path,
    custodian_role_managed_policy_arns,
    custodian_c7n_version,
    organization,
):
    create_custodian_role(
        task_to_add,
        all_tasks,
        custodian_account_id,
        custodian_account_id,
        custodian_region,
        custodian_role_name,
        custodian_role_path,
        custodian_role_managed_policy_arns,
    )
    prepare_account_as_hub(
        task_to_add,
        all_tasks,
        custodian_account_id,
        custodian_region,
        custodian_role_name,
        custodian_role_path,
        custodian_c7n_version,
        organization,
    )
    forward_events_account_task(
        task_to_add,
        all_tasks,
        custodian_account_id,
        custodian_account_id,
        custodian_region,
    )
    forward_events_region_task(
        task_to_add,
        all_tasks,
        custodian_account_id,
        region,
        custodian_account_id,
        custodian_region,
    )


def handle_c7n_aws_cloudtrails_for_spoke(
    task_to_add,
    all_tasks,
    account_id,
    region,
    custodian_account_id,
    custodian_region,
    custodian_role_name,
    custodian_role_path,
    custodian_role_managed_policy_arns,
):
    create_custodian_role(
        task_to_add,
        all_tasks,
        account_id,
        custodian_account_id,
        custodian_region,
        custodian_role_name,
        custodian_role_path,
        custodian_role_managed_policy_arns,
    )
    forward_events_account_task(
        task_to_add, all_tasks, account_id, custodian_account_id, custodian_region
    )
    forward_events_region_task(
        task_to_add,
        all_tasks,
        account_id,
        region,
        custodian_account_id,
        custodian_region,
    )


def get_organization_for_account(manifest, account_id):
    for a in manifest.get("accounts"):
        if str(a.get("account_id")) == str(account_id):
            return a["organization"]


def get_custodian_region(manifest, account_id):
    for a in manifest.get("accounts"):
        if str(a.get("account_id")) == str(account_id):
            return a["default_region"]


def handle_c7n_aws_cloudtrails(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
    manifest,
):
    account_id = task_to_add.get("account_id")
    region = task_to_add.get("region")
    custodian_account_id = task_to_add.get("custodian")
    custodian_role_name = task_to_add.get("role_name")
    custodian_role_path = task_to_add.get("role_path")
    custodian_role_managed_policy_arns = task_to_add.get("role_managed_policy_arns")
    custodian_c7n_version = task_to_add.get("c7n_version")
    organization = get_organization_for_account(manifest, account_id)
    custodian_region = get_custodian_region(manifest, custodian_account_id)

    handle_c7n_aws_cloudtrails_for_custodian(
        task_to_add,
        all_tasks,
        region,
        custodian_account_id,
        custodian_region,
        custodian_role_name,
        custodian_role_path,
        custodian_role_managed_policy_arns,
        custodian_c7n_version,
        organization,
    )
    handle_c7n_aws_cloudtrails_for_spoke(
        task_to_add,
        all_tasks,
        account_id,
        region,
        custodian_account_id,
        custodian_region,
        custodian_role_name,
        custodian_role_path,
        custodian_role_managed_policy_arns,
    )

    deploy_policies(
        task_to_add,
        all_tasks,
        account_id,
        region,
        custodian_account_id,
        custodian_region,
        custodian_role_name,
        custodian_role_path,
    )

    del all_tasks[all_tasks_task_reference]
