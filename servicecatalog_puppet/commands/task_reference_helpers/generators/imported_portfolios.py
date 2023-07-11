#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import config, constants, task_reference_constants
from servicecatalog_puppet.commands.task_reference_helpers.generators import portfolios


def get_imported_portfolio_common_args(
    task_to_add, all_tasks_task_reference, extra_dependencies_by_reference=[]
):
    return dict(
        status=task_to_add.get("status"),
        account_id=task_to_add.get("account_id"),
        region=task_to_add.get("region"),
        portfolio=task_to_add.get("portfolio"),
        execution=task_to_add.get("execution"),
        dependencies_by_reference=[all_tasks_task_reference]
        + extra_dependencies_by_reference,
        portfolio_task_reference=all_tasks_task_reference,
    )


def add_puppet_associations_for_when_not_sharing_with_puppet_account(
    all_tasks,
    all_tasks_task_reference,
    puppet_account_id,
    task_to_add,
    hub_portfolio_ref,
    dependencies_for_import_portfolios_sub_tasks,
):
    # GET THE HUB PORTFOLIO
    if not all_tasks.get(hub_portfolio_ref):
        all_tasks[hub_portfolio_ref] = {
            "puppet_account_id": puppet_account_id,
            "task_reference": hub_portfolio_ref,
            "dependencies_by_reference": [],
            "account_id": puppet_account_id,
            "region": task_to_add.get("region"),
            "portfolio": task_to_add.get("portfolio"),
            "status": task_to_add.get("status"),
            "execution": task_to_add.get("execution"),
            "section_name": constants.PORTFOLIO_LOCAL,
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
        }
    all_tasks[hub_portfolio_ref][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[hub_portfolio_ref][task_reference_constants.MANIFEST_ITEM_NAMES].update(
        task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES)
    )
    all_tasks[hub_portfolio_ref][task_reference_constants.MANIFEST_ACCOUNT_IDS].update(
        task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
    )
    del all_tasks[all_tasks_task_reference]
    # all_tasks[all_tasks_task_reference]["portfolio_task_reference"] = hub_portfolio_ref
    # all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
    #     hub_portfolio_ref
    # )

    # CREATE THE HUB ASSOCIATIONS
    hub_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
    if not all_tasks.get(hub_portfolio_puppet_association_ref):
        all_tasks[hub_portfolio_puppet_association_ref] = {
            "puppet_account_id": puppet_account_id,
            "task_reference": hub_portfolio_puppet_association_ref,
            "portfolio_task_reference": hub_portfolio_ref,
            "dependencies_by_reference": [
                hub_portfolio_ref,
                constants.CREATE_POLICIES,
            ],
            "account_id": puppet_account_id,
            "region": task_to_add.get("region"),
            "portfolio": task_to_add.get("portfolio"),
            "execution": task_to_add.get("execution"),
            "section_name": constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
        }
    all_tasks[hub_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[hub_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_ITEM_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES))
    all_tasks[hub_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_ACCOUNT_IDS
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))

    # CREATE SPOKE ASSOCIATIONS
    spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
    if not all_tasks.get(spoke_portfolio_puppet_association_ref):
        all_tasks[spoke_portfolio_puppet_association_ref] = {
            "puppet_account_id": puppet_account_id,
            "task_reference": spoke_portfolio_puppet_association_ref,
            "portfolio_task_reference": hub_portfolio_ref,
            "dependencies_by_reference": [hub_portfolio_ref, constants.CREATE_POLICIES,]
            + dependencies_for_import_portfolios_sub_tasks,
            "account_id": task_to_add.get("account_id"),
            "region": task_to_add.get("region"),
            "portfolio": task_to_add.get("portfolio"),
            "execution": task_to_add.get("execution"),
            "section_name": constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
        }
    all_tasks[spoke_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[spoke_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_ITEM_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES))
    all_tasks[spoke_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_ACCOUNT_IDS
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))

    return hub_portfolio_ref


def setup_sharing_for_portfolio(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
    hub_portfolio_ref,
):
    # SHARE THE PORTFOLIO
    sharing_mode = task_to_add.get(
        "sharing_mode", config.get_global_sharing_mode_default()
    )
    if sharing_mode == constants.SHARING_MODE_ACCOUNT:
        share_and_accept_ref = f"portfolio_share_and_accept-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        sharing_type = "ACCOUNT"
    elif sharing_mode == constants.SHARING_MODE_AWS_ORGANIZATIONS:
        share_and_accept_ref = f"portfolio_share_and_accept-{task_to_add.get('ou')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        sharing_type = (
            "ORGANIZATIONAL_UNIT"
            if task_to_add.get("ou")[0:3] == "ou-"
            else "ORGANIZATION"
        )
    else:
        raise Exception(f"Unknown sharing mode: {sharing_mode}")

    describe_portfolio_shares_task_ref = portfolios.get_or_create_describe_portfolio_shares_task_ref(
        all_tasks, puppet_account_id, sharing_type, hub_portfolio_ref, task_to_add,
    )

    if not all_tasks.get(share_and_accept_ref):
        all_tasks[share_and_accept_ref] = {
            "puppet_account_id": puppet_account_id,
            "account_id": task_to_add.get("account_id"),
            "region": task_to_add.get("region"),
            "task_reference": share_and_accept_ref,
            "share_tag_options": task_to_add.get("share_tag_options"),
            "share_principals": task_to_add.get("share_principals"),
            "dependencies_by_reference": [
                hub_portfolio_ref,
                constants.CREATE_POLICIES,
                describe_portfolio_shares_task_ref,
            ],
            "describe_portfolio_shares_task_ref": describe_portfolio_shares_task_ref,
            "portfolio": task_to_add.get("portfolio"),
            "execution": task_to_add.get("execution"),
            "portfolio_task_reference": hub_portfolio_ref,
            "section_name": f"portfolio-share-and-accept-{sharing_mode.lower()}",
            "ou_to_share_with": task_to_add.get("ou"),
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
        }
    all_tasks[share_and_accept_ref][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[share_and_accept_ref][
        task_reference_constants.MANIFEST_ITEM_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES))
    all_tasks[share_and_accept_ref][
        task_reference_constants.MANIFEST_ACCOUNT_IDS
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))
    return share_and_accept_ref


def handle_imported_portfolios(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    is_sharing_with_puppet_account = task_to_add.get("account_id") == puppet_account_id
    #
    if task_to_add.get("status") == constants.TERMINATED:
        # DELETE THE ASSOCIATION IF IT EXISTS
        if task_to_add.get("associations"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"portfolio_associations-{shared_ref}"
            if not all_tasks.get(ref):
                all_tasks[ref] = {
                    "status": task_to_add.get("status"),
                    "account_id": task_to_add.get("account_id"),
                    "region": task_to_add.get("region"),
                    "portfolio": task_to_add.get("portfolio"),
                    "execution": task_to_add.get("execution"),
                    "dependencies_by_reference": [constants.CREATE_POLICIES],
                    "task_reference": ref,
                    "spoke_local_portfolio_name": item_name,
                    "section_name": constants.PORTFOLIO_ASSOCIATIONS,
                    "associations": task_to_add.get("associations"),
                    task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
                    task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
                    task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
                }
            all_tasks[ref][task_reference_constants.MANIFEST_SECTION_NAMES].update(
                task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES)
            )
            all_tasks[ref][task_reference_constants.MANIFEST_ITEM_NAMES].update(
                task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES)
            )
            all_tasks[ref][task_reference_constants.MANIFEST_ACCOUNT_IDS].update(
                task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
            )
            del all_tasks[
                all_tasks_task_reference
            ]  # DO NOT NEED THIS TASK TO DO ANYTHING AT THE MOMENT
    else:
        dependencies_for_import_portfolios_sub_tasks = list()
        if is_sharing_with_puppet_account:
            target_portfolio_ref = add_puppet_associations_for_when_sharing_with_puppet_account(
                all_tasks, all_tasks_task_reference, puppet_account_id, task_to_add
            )

        else:
            hub_portfolio_ref = f"{constants.PORTFOLIO_LOCAL}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            share_and_accept_ref = setup_sharing_for_portfolio(
                all_tasks,
                all_tasks_task_reference,
                item_name,
                puppet_account_id,
                section_name,
                task_reference,
                task_to_add,
                hub_portfolio_ref,
            )
            dependencies_for_import_portfolios_sub_tasks.append(share_and_accept_ref)
            target_portfolio_ref = add_puppet_associations_for_when_not_sharing_with_puppet_account(
                all_tasks,
                all_tasks_task_reference,
                puppet_account_id,
                task_to_add,
                hub_portfolio_ref,
                dependencies_for_import_portfolios_sub_tasks,
            )

        # need to add the sharing tasks to the dependencies
        if task_to_add.get("associations"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"portfolio_associations-{shared_ref}"
            all_tasks[ref] = dict(
                **get_imported_portfolio_common_args(
                    task_to_add,
                    target_portfolio_ref,
                    [constants.CREATE_POLICIES]
                    + dependencies_for_import_portfolios_sub_tasks,
                ),
                task_reference=ref,
                spoke_local_portfolio_name=item_name,
                section_name=constants.PORTFOLIO_ASSOCIATIONS,
                associations=task_to_add.get("associations"),
            )
            all_tasks[ref][task_reference_constants.MANIFEST_SECTION_NAMES] = dict(
                **task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES)
            )
            all_tasks[ref][task_reference_constants.MANIFEST_ITEM_NAMES] = dict(
                **task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES)
            )
            all_tasks[ref][task_reference_constants.MANIFEST_ACCOUNT_IDS] = dict(
                **task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
            )

    if task_to_add.get("was_a_spoke_local_portfolio"):
        # DELETE THE LAUNCH CONSTRAINTS IF IT EXISTS
        shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
        ref = f"launch_constraints-{shared_ref}"
        if not all_tasks.get(ref):
            all_tasks[ref] = {
                "status": constants.TERMINATED,
                "account_id": task_to_add.get("account_id"),
                "region": task_to_add.get("region"),
                "portfolio": task_to_add.get("portfolio"),
                "execution": task_to_add.get("execution"),
                "dependencies_by_reference": [constants.CREATE_POLICIES]
                + dependencies_for_import_portfolios_sub_tasks,
                "task_reference": ref,
                "section_name": constants.PORTFOLIO_CONSTRAINTS_LAUNCH,
                "spoke_local_portfolio_name": item_name,
                "launch_constraints": task_to_add.get("launch_constraints"),
                task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
                task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
                task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            }
        all_tasks[ref][task_reference_constants.MANIFEST_SECTION_NAMES].update(
            task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES)
        )
        all_tasks[ref][task_reference_constants.MANIFEST_ITEM_NAMES].update(
            task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES)
        )
        all_tasks[ref][task_reference_constants.MANIFEST_ACCOUNT_IDS].update(
            task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
        )
        # DELETE THE RESOURCE UPDATE CONSTRAINTS IF IT EXISTS
        shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
        ref = f"resource_update_constraints-{shared_ref}"
        if not all_tasks.get(ref):
            all_tasks[ref] = {
                "status": constants.TERMINATED,
                "account_id": task_to_add.get("account_id"),
                "region": task_to_add.get("region"),
                "portfolio": task_to_add.get("portfolio"),
                "execution": task_to_add.get("execution"),
                "dependencies_by_reference": [constants.CREATE_POLICIES]
                + dependencies_for_import_portfolios_sub_tasks,
                "task_reference": ref,
                "section_name": constants.PORTFOLIO_CONSTRAINTS_RESOURCE_UPDATE,
                "resource_update_constraints": task_to_add.get(
                    "resource_update_constraints"
                ),
                "spoke_local_portfolio_name": item_name,
                task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
                task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
                task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            }
        all_tasks[ref][task_reference_constants.MANIFEST_SECTION_NAMES].update(
            task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES)
        )
        all_tasks[ref][task_reference_constants.MANIFEST_ITEM_NAMES].update(
            task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES)
        )
        all_tasks[ref][task_reference_constants.MANIFEST_ACCOUNT_IDS].update(
            task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS)
        )


def add_puppet_associations_for_when_sharing_with_puppet_account(
    all_tasks, all_tasks_task_reference, puppet_account_id, task_to_add
):
    # CREATE SPOKE ASSOCIATIONS
    spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
    if not all_tasks.get(spoke_portfolio_puppet_association_ref):
        all_tasks[spoke_portfolio_puppet_association_ref] = {
            "puppet_account_id": puppet_account_id,
            "task_reference": spoke_portfolio_puppet_association_ref,
            "portfolio_task_reference": all_tasks_task_reference,
            "dependencies_by_reference": [
                all_tasks_task_reference,
                constants.CREATE_POLICIES,
            ],
            "account_id": task_to_add.get("account_id"),
            "region": task_to_add.get("region"),
            "portfolio": task_to_add.get("portfolio"),
            "execution": task_to_add.get("execution"),
            "section_name": constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
            task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
            task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
        }
    all_tasks[spoke_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_SECTION_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_SECTION_NAMES))
    all_tasks[spoke_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_ITEM_NAMES
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ITEM_NAMES))
    all_tasks[spoke_portfolio_puppet_association_ref][
        task_reference_constants.MANIFEST_ACCOUNT_IDS
    ].update(task_to_add.get(task_reference_constants.MANIFEST_ACCOUNT_IDS))
    return spoke_portfolio_puppet_association_ref
