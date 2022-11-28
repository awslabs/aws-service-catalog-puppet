#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants, config
from servicecatalog_puppet.commands.task_reference_helpers.generators import portfolios


def get_spoke_local_portfolio_common_args(
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


def handle_spoke_local_portfolios(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    is_sharing_with_puppet_account = task_to_add.get("account_id") == puppet_account_id

    if task_to_add.get("status") == constants.TERMINATED:
        deps = list()
        # DELETE THE ASSOCIATION IF IT EXISTS
        if task_to_add.get("associations"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"portfolio_associations-{shared_ref}"
            deps.append(ref)
            if not all_tasks.get(ref):
                all_tasks[ref] = dict(
                    status=task_to_add.get("status"),
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    execution=task_to_add.get("execution"),
                    dependencies_by_reference=[constants.CREATE_POLICIES],
                    task_reference=ref,
                    spoke_local_portfolio_name=item_name,
                    section_name=constants.PORTFOLIO_ASSOCIATIONS,
                    associations=task_to_add.get("associations"),
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[ref]["manifest_section_names"].update(
                task_to_add.get("manifest_section_names")
            )
            all_tasks[ref]["manifest_item_names"].update(
                task_to_add.get("manifest_item_names")
            )
            all_tasks[ref]["manifest_account_ids"].update(
                task_to_add.get("manifest_account_ids")
            )
        # DELETE THE LAUNCH CONSTRAINTS IF IT EXISTS
        if task_to_add.get("launch_constraints"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"launch_constraints-{shared_ref}"
            deps.append(ref)
            if not all_tasks.get(ref):
                all_tasks[ref] = dict(
                    status=task_to_add.get("status"),
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    execution=task_to_add.get("execution"),
                    dependencies_by_reference=[constants.CREATE_POLICIES],
                    task_reference=ref,
                    section_name=constants.PORTFOLIO_CONSTRAINTS_LAUNCH,
                    spoke_local_portfolio_name=item_name,
                    launch_constraints=task_to_add["launch_constraints"],
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[ref]["manifest_section_names"].update(
                task_to_add.get("manifest_section_names")
            )
            all_tasks[ref]["manifest_item_names"].update(
                task_to_add.get("manifest_item_names")
            )
            all_tasks[ref]["manifest_account_ids"].update(
                task_to_add.get("manifest_account_ids")
            )
        # DELETE THE RESOURCE UPDATE CONSTRAINTS IF IT EXISTS
        if task_to_add.get("resource_update_constraints"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"resource_update_constraints-{shared_ref}"
            deps.append(ref)
            if not all_tasks.get(ref):
                all_tasks[ref] = dict(
                    status=task_to_add.get("status"),
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    execution=task_to_add.get("execution"),
                    dependencies_by_reference=[constants.CREATE_POLICIES],
                    task_reference=ref,
                    section_name=constants.PORTFOLIO_CONSTRAINTS_RESOURCE_UPDATE,
                    spoke_local_portfolio_name=item_name,
                    resource_update_constraints=task_to_add[
                        "resource_update_constraints"
                    ],
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[ref]["manifest_section_names"].update(
                task_to_add.get("manifest_section_names")
            )
            all_tasks[ref]["manifest_item_names"].update(
                task_to_add.get("manifest_item_names")
            )
            all_tasks[ref]["manifest_account_ids"].update(
                task_to_add.get("manifest_account_ids")
            )
        # GET THE SPOKE LOCAL PORTFOLIO SO WE CAN DELETE THE ASSOCIATIONS
        spoke_portfolio_ref = f"{constants.PORTFOLIO_LOCAL}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        if not all_tasks.get(spoke_portfolio_ref):
            all_tasks[spoke_portfolio_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=spoke_portfolio_ref,
                dependencies_by_reference=[constants.CREATE_POLICIES],
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                status=task_to_add.get("status"),
                execution=task_to_add.get("execution"),
                section_name=constants.PORTFOLIO_LOCAL,
                manifest_section_names=dict(),
                manifest_item_names=dict(),
                manifest_account_ids=dict(),
            )
        all_tasks[spoke_portfolio_ref]["manifest_section_names"].update(
            task_to_add.get("manifest_section_names")
        )
        all_tasks[spoke_portfolio_ref]["manifest_item_names"].update(
            task_to_add.get("manifest_item_names")
        )
        all_tasks[spoke_portfolio_ref]["manifest_account_ids"].update(
            task_to_add.get("manifest_account_ids")
        )

        if not is_sharing_with_puppet_account:
            # GET THE SPOKE PRODUCTS AND VERSIONS SO WE CAN DISASSOCIATE THEM
            spoke_portfolio_all_products_and_versions_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(spoke_portfolio_all_products_and_versions_ref):
                all_tasks[spoke_portfolio_all_products_and_versions_ref] = dict(
                    execution=task_to_add.get("execution"),
                    puppet_account_id=puppet_account_id,
                    task_reference=spoke_portfolio_all_products_and_versions_ref,
                    dependencies_by_reference=[spoke_portfolio_ref],
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    portfolio_task_reference=spoke_portfolio_ref,
                    section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[spoke_portfolio_all_products_and_versions_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))

            disassociate_portfolio_all_products_and_versions_ref = f"{constants.PORTFOLIO_DISASSOCIATE_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(disassociate_portfolio_all_products_and_versions_ref):
                all_tasks[disassociate_portfolio_all_products_and_versions_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=disassociate_portfolio_all_products_and_versions_ref,
                    dependencies_by_reference=[
                        spoke_portfolio_all_products_and_versions_ref,
                        spoke_portfolio_ref,
                        constants.CREATE_POLICIES,
                    ],
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    portfolio_task_reference=spoke_portfolio_ref,
                    section_name=constants.PORTFOLIO_DISASSOCIATE_ALL_PRODUCTS_AND_THEIR_VERSIONS,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[disassociate_portfolio_all_products_and_versions_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[disassociate_portfolio_all_products_and_versions_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[disassociate_portfolio_all_products_and_versions_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))

            deps.append(disassociate_portfolio_all_products_and_versions_ref)

        # DELETE THE SPOKE LOCAL PORTFOLIO ASSOCIATION
        spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        if not all_tasks.get(spoke_portfolio_puppet_association_ref):
            all_tasks[spoke_portfolio_puppet_association_ref] = dict(
                status=task_to_add.get("status"),
                puppet_account_id=puppet_account_id,
                task_reference=spoke_portfolio_puppet_association_ref,
                portfolio_task_reference=spoke_portfolio_ref,
                dependencies_by_reference=[
                    spoke_portfolio_ref,
                    constants.CREATE_POLICIES,
                ],
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                execution=task_to_add.get("execution"),
                section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
                manifest_section_names=dict(),
                manifest_item_names=dict(),
                manifest_account_ids=dict(),
            )
        all_tasks[spoke_portfolio_puppet_association_ref][
            "manifest_section_names"
        ].update(task_to_add.get("manifest_section_names"))
        all_tasks[spoke_portfolio_puppet_association_ref]["manifest_item_names"].update(
            task_to_add.get("manifest_item_names")
        )
        all_tasks[spoke_portfolio_puppet_association_ref][
            "manifest_account_ids"
        ].update(task_to_add.get("manifest_account_ids"))
        deps.append(spoke_portfolio_puppet_association_ref)

        task_to_add["dependencies_by_reference"].extend(deps)

    else:
        dependencies_for_constraints = list()
        if is_sharing_with_puppet_account:
            # CREATE SPOKE ASSOCIATIONS
            spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(spoke_portfolio_puppet_association_ref):
                all_tasks[spoke_portfolio_puppet_association_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=spoke_portfolio_puppet_association_ref,
                    portfolio_task_reference=all_tasks_task_reference,
                    dependencies_by_reference=[
                        all_tasks_task_reference,
                        constants.CREATE_POLICIES,
                    ],
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    execution=task_to_add.get("execution"),
                    section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[spoke_portfolio_puppet_association_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[spoke_portfolio_puppet_association_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[spoke_portfolio_puppet_association_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))

            # GET THE SPOKE PRODUCTS AND VERSIONS - USE THE AFTER ONE AS NO PRODUCTS WILL BE COPIED WHEN SHARING WITH PUPPET ACCOUNT
            spoke_portfolio_all_products_and_versions_after_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-after-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(spoke_portfolio_all_products_and_versions_after_ref):
                all_tasks[spoke_portfolio_all_products_and_versions_after_ref] = dict(
                    **get_spoke_local_portfolio_common_args(
                        task_to_add,
                        all_tasks_task_reference,
                        [spoke_portfolio_puppet_association_ref],
                    ),
                    task_reference=spoke_portfolio_all_products_and_versions_after_ref,
                    section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[spoke_portfolio_all_products_and_versions_after_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_after_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_after_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))
            dependencies_for_constraints.append(
                spoke_portfolio_all_products_and_versions_after_ref
            )

        else:
            # GET THE HUB PORTFOLIO
            hub_portfolio_ref = f"{constants.PORTFOLIO_LOCAL}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(hub_portfolio_ref):
                all_tasks[hub_portfolio_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=hub_portfolio_ref,
                    dependencies_by_reference=[],
                    account_id=puppet_account_id,
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    status=task_to_add.get("status"),
                    execution=task_to_add.get("execution"),
                    section_name=constants.PORTFOLIO_LOCAL,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[hub_portfolio_ref]["manifest_section_names"].update(
                task_to_add.get("manifest_section_names")
            )
            all_tasks[hub_portfolio_ref]["manifest_item_names"].update(
                task_to_add.get("manifest_item_names")
            )
            all_tasks[hub_portfolio_ref]["manifest_account_ids"].update(
                task_to_add.get("manifest_account_ids")
            )
            all_tasks[all_tasks_task_reference][
                "portfolio_task_reference"
            ] = hub_portfolio_ref
            all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
                hub_portfolio_ref
            )

            # CREATE THE HUB ASSOCIATIONS
            hub_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(hub_portfolio_puppet_association_ref):
                all_tasks[hub_portfolio_puppet_association_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=hub_portfolio_puppet_association_ref,
                    portfolio_task_reference=hub_portfolio_ref,
                    dependencies_by_reference=[
                        hub_portfolio_ref,
                        constants.CREATE_POLICIES,
                    ],
                    account_id=puppet_account_id,
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    execution=task_to_add.get("execution"),
                    section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,  # TODO test in with a new spoke local
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[hub_portfolio_puppet_association_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[hub_portfolio_puppet_association_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[hub_portfolio_puppet_association_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))

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
                all_tasks,
                puppet_account_id,
                sharing_type,
                hub_portfolio_ref,
                task_to_add,
            )

            if not all_tasks.get(share_and_accept_ref):
                all_tasks[share_and_accept_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    task_reference=share_and_accept_ref,
                    share_tag_options=task_to_add.get("share_tag_options"),
                    share_principals=task_to_add.get("share_principals"),
                    dependencies_by_reference=[
                        hub_portfolio_ref,
                        constants.CREATE_POLICIES,
                        describe_portfolio_shares_task_ref,
                    ],
                    describe_portfolio_shares_task_ref=describe_portfolio_shares_task_ref,
                    portfolio=task_to_add.get("portfolio"),
                    execution=task_to_add.get("execution"),
                    portfolio_task_reference=hub_portfolio_ref,
                    section_name=f"portfolio-share-and-accept-{sharing_mode.lower()}",
                    ou_to_share_with=task_to_add.get("ou"),
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[share_and_accept_ref]["manifest_section_names"].update(
                task_to_add.get("manifest_section_names")
            )
            all_tasks[share_and_accept_ref]["manifest_item_names"].update(
                task_to_add.get("manifest_item_names")
            )
            all_tasks[share_and_accept_ref]["manifest_account_ids"].update(
                task_to_add.get("manifest_account_ids")
            )

            # GET THE HUB PRODUCTS AND VERSIONS SO WE KNOW WHAT NEEDS TO BE COPIED OR IMPORTED
            hub_portfolio_all_products_and_versions_before_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-before-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(hub_portfolio_all_products_and_versions_before_ref):
                all_tasks[hub_portfolio_all_products_and_versions_before_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=hub_portfolio_all_products_and_versions_before_ref,
                    dependencies_by_reference=[
                        hub_portfolio_ref,
                        hub_portfolio_puppet_association_ref,  # TODO reduce this down to one ?
                    ],
                    portfolio_task_reference=hub_portfolio_ref,
                    account_id=puppet_account_id,
                    region=task_to_add.get("region"),
                    execution=task_to_add.get("execution"),
                    section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[hub_portfolio_all_products_and_versions_before_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[hub_portfolio_all_products_and_versions_before_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[hub_portfolio_all_products_and_versions_before_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))

            # CREATE SPOKE ASSOCIATIONS
            spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(spoke_portfolio_puppet_association_ref):
                all_tasks[spoke_portfolio_puppet_association_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=spoke_portfolio_puppet_association_ref,
                    portfolio_task_reference=all_tasks_task_reference,
                    dependencies_by_reference=[
                        all_tasks_task_reference,
                        constants.CREATE_POLICIES,
                    ],
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    portfolio=task_to_add.get("portfolio"),
                    execution=task_to_add.get("execution"),
                    section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[spoke_portfolio_puppet_association_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[spoke_portfolio_puppet_association_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[spoke_portfolio_puppet_association_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))

            # GET THE SPOKE PRODUCTS AND VERSIONS SO WE KNOW WHAT IS MISSING OR NEEDS UPDATING
            spoke_portfolio_all_products_and_versions_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(spoke_portfolio_all_products_and_versions_ref):
                all_tasks[spoke_portfolio_all_products_and_versions_ref] = dict(
                    **get_spoke_local_portfolio_common_args(
                        task_to_add,
                        all_tasks_task_reference,
                        [spoke_portfolio_puppet_association_ref],
                    ),
                    task_reference=spoke_portfolio_all_products_and_versions_ref,
                    section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[spoke_portfolio_all_products_and_versions_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))

            # COPY OR IMPORT THE CHANGES BETWEEN THE TWO PORTFOLIOS
            product_generation_method = task_to_add.get("product_generation_method")
            portfolio_import_or_copy_ref = f"portfolio_{product_generation_method}-{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            portfolio_import_or_copy_task = dict(
                **get_spoke_local_portfolio_common_args(
                    task_to_add,
                    all_tasks_task_reference,
                    [
                        spoke_portfolio_all_products_and_versions_ref,
                        hub_portfolio_all_products_and_versions_before_ref,
                    ],
                ),
                task_reference=portfolio_import_or_copy_ref,
                product_generation_mathod=product_generation_method,
                section_name=f"portfolio-{product_generation_method}",
                portfolio_get_all_products_and_their_versions_ref=spoke_portfolio_all_products_and_versions_ref,
                portfolio_get_all_products_and_their_versions_for_hub_ref=hub_portfolio_all_products_and_versions_before_ref,
                manifest_section_names=dict(
                    **task_to_add.get("manifest_section_names")
                ),
                manifest_item_names=dict(**task_to_add.get("manifest_item_names")),
                manifest_account_ids=dict(**task_to_add.get("manifest_account_ids")),
            )
            if product_generation_method == constants.PRODUCT_GENERATION_METHOD_IMPORT:
                portfolio_import_or_copy_task[
                    "hub_portfolio_task_reference"
                ] = hub_portfolio_ref
                portfolio_import_or_copy_task["dependencies_by_reference"].append(
                    hub_portfolio_ref
                )
            all_tasks[portfolio_import_or_copy_ref] = portfolio_import_or_copy_task
            dependencies_for_constraints.append(portfolio_import_or_copy_ref)

        if task_to_add.get("associations"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"portfolio_associations-{shared_ref}"
            all_tasks[ref] = dict(
                **get_spoke_local_portfolio_common_args(
                    task_to_add, all_tasks_task_reference, [constants.CREATE_POLICIES],
                ),
                task_reference=ref,
                spoke_local_portfolio_name=item_name,
                section_name=constants.PORTFOLIO_ASSOCIATIONS,
                associations=task_to_add.get("associations"),
                manifest_section_names=dict(
                    **task_to_add.get("manifest_section_names")
                ),
                manifest_item_names=dict(**task_to_add.get("manifest_item_names")),
                manifest_account_ids=dict(**task_to_add.get("manifest_account_ids")),
            )
        if not is_sharing_with_puppet_account:
            # GET NEW PRODUCT AND VERSIONS FOLLOWING THE IMPORT OR COPY
            spoke_portfolio_all_products_and_versions_after_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-after-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            if not all_tasks.get(spoke_portfolio_all_products_and_versions_after_ref):
                all_tasks[spoke_portfolio_all_products_and_versions_after_ref] = dict(
                    **get_spoke_local_portfolio_common_args(
                        task_to_add,
                        all_tasks_task_reference,
                        [
                            spoke_portfolio_puppet_association_ref,
                            portfolio_import_or_copy_ref,
                        ],
                    ),
                    task_reference=spoke_portfolio_all_products_and_versions_after_ref,
                    section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
                    manifest_section_names=dict(),
                    manifest_item_names=dict(),
                    manifest_account_ids=dict(),
                )
            all_tasks[spoke_portfolio_all_products_and_versions_after_ref][
                "manifest_section_names"
            ].update(task_to_add.get("manifest_section_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_after_ref][
                "manifest_item_names"
            ].update(task_to_add.get("manifest_item_names"))
            all_tasks[spoke_portfolio_all_products_and_versions_after_ref][
                "manifest_account_ids"
            ].update(task_to_add.get("manifest_account_ids"))
            dependencies_for_constraints.append(
                spoke_portfolio_all_products_and_versions_after_ref,
            )

        if task_to_add.get("launch_constraints"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"launch_constraints-{shared_ref}"
            all_tasks[ref] = dict(
                **get_spoke_local_portfolio_common_args(
                    task_to_add, all_tasks_task_reference, dependencies_for_constraints,
                ),
                task_reference=ref,
                section_name=constants.PORTFOLIO_CONSTRAINTS_LAUNCH,
                spoke_local_portfolio_name=item_name,
                launch_constraints=task_to_add["launch_constraints"],
                portfolio_get_all_products_and_their_versions_ref=spoke_portfolio_all_products_and_versions_after_ref,
                manifest_section_names=dict(
                    **task_to_add.get("manifest_section_names")
                ),
                manifest_item_names=dict(**task_to_add.get("manifest_item_names")),
                manifest_account_ids=dict(**task_to_add.get("manifest_account_ids")),
            )
        if task_to_add.get("resource_update_constraints"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"resource_update_constraints-{shared_ref}"
            all_tasks[ref] = dict(
                **get_spoke_local_portfolio_common_args(
                    task_to_add, all_tasks_task_reference, dependencies_for_constraints,
                ),
                task_reference=ref,
                section_name=constants.PORTFOLIO_CONSTRAINTS_RESOURCE_UPDATE,
                spoke_local_portfolio_name=item_name,
                resource_update_constraints=task_to_add["resource_update_constraints"],
                portfolio_get_all_products_and_their_versions_ref=spoke_portfolio_all_products_and_versions_after_ref,
                manifest_section_names=dict(
                    **task_to_add.get("manifest_section_names")
                ),
                manifest_item_names=dict(**task_to_add.get("manifest_item_names")),
                manifest_account_ids=dict(**task_to_add.get("manifest_account_ids")),
            )
