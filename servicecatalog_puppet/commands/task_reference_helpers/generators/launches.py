#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants, config
from servicecatalog_puppet.commands.task_reference_helpers.generators import portfolios


def handle_launches(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    is_deploying_into_puppet_account = (
        task_to_add.get("account_id") == puppet_account_id
    )
    # GET THE HUB DETAILS TASK
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
            execution=constants.EXECUTION_MODE_HUB,
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

    spoke_portfolio_puppet_association_ref = None
    if is_deploying_into_puppet_account:
        portfolio_deploying_from = hub_portfolio_ref
    else:
        # share the portfolio and accept it
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
            all_tasks, puppet_account_id, sharing_type, hub_portfolio_ref, task_to_add
        )

        if not all_tasks.get(share_and_accept_ref):
            all_tasks[share_and_accept_ref] = dict(
                puppet_account_id=puppet_account_id,
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                share_tag_options=task_to_add.get("share_tag_options"),
                share_principals=task_to_add.get("share_principals"),
                task_reference=share_and_accept_ref,
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

        # GET THE IMPORTED PORTFOLIO
        spoke_portfolio_ref = f"{constants.PORTFOLIO_IMPORTED}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        if not all_tasks.get(spoke_portfolio_ref):
            all_tasks[spoke_portfolio_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=spoke_portfolio_ref,
                dependencies_by_reference=[share_and_accept_ref],
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                sharing_mode=task_to_add.get(
                    "sharing_mode", config.get_global_sharing_mode_default()
                ),
                section_name=constants.PORTFOLIO_IMPORTED,
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
        portfolio_deploying_from = spoke_portfolio_ref

        spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        if not all_tasks.get(spoke_portfolio_puppet_association_ref):
            all_tasks[spoke_portfolio_puppet_association_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=spoke_portfolio_puppet_association_ref,
                portfolio_task_reference=spoke_portfolio_ref,
                dependencies_by_reference=[spoke_portfolio_ref],
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

        all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
            spoke_portfolio_puppet_association_ref
        )

    # GET the provisioning parameters
    describe_provisioning_params_ref = f"{constants.DESCRIBE_PROVISIONING_PARAMETERS}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}-{task_to_add.get('product')}-{task_to_add.get('version')}"
    if not all_tasks.get(describe_provisioning_params_ref):
        all_tasks[describe_provisioning_params_ref] = dict(
            puppet_account_id=puppet_account_id,
            task_reference=describe_provisioning_params_ref,
            dependencies_by_reference=[
                hub_portfolio_ref,
                # TODO check this still works for a new portfolio after changing it from: portfolio_deploying_from
            ],  # associations are added here and so this is a dependency
            account_id=puppet_account_id,
            region=task_to_add.get("region"),
            portfolio=task_to_add.get("portfolio"),
            product=task_to_add.get("product"),
            version=task_to_add.get("version"),
            section_name=constants.DESCRIBE_PROVISIONING_PARAMETERS,
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
        )
    all_tasks[describe_provisioning_params_ref]["manifest_section_names"].update(
        task_to_add.get("manifest_section_names")
    )
    all_tasks[describe_provisioning_params_ref]["manifest_item_names"].update(
        task_to_add.get("manifest_item_names")
    )
    all_tasks[describe_provisioning_params_ref]["manifest_account_ids"].update(
        task_to_add.get("manifest_account_ids")
    )

    # GET all the products for the spoke
    if spoke_portfolio_puppet_association_ref is None:
        deps = [portfolio_deploying_from]
    else:
        deps = [portfolio_deploying_from, spoke_portfolio_puppet_association_ref]
    portfolio_get_all_products_and_their_versions_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{task_to_add.get('account_id')}-{section_name}-{item_name}--{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
    if not all_tasks.get(portfolio_get_all_products_and_their_versions_ref):
        all_tasks[portfolio_get_all_products_and_their_versions_ref] = dict(
            execution=task_to_add.get("execution"),
            puppet_account_id=puppet_account_id,
            task_reference=portfolio_get_all_products_and_their_versions_ref,
            dependencies_by_reference=deps,
            portfolio_task_reference=portfolio_deploying_from,
            account_id=puppet_account_id,
            region=task_to_add.get("region"),
            section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
        )
    all_tasks[portfolio_get_all_products_and_their_versions_ref][
        "manifest_section_names"
    ].update(task_to_add.get("manifest_section_names"))
    all_tasks[portfolio_get_all_products_and_their_versions_ref][
        "manifest_item_names"
    ].update(task_to_add.get("manifest_item_names"))
    all_tasks[portfolio_get_all_products_and_their_versions_ref][
        "manifest_account_ids"
    ].update(task_to_add.get("manifest_account_ids"))

    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        portfolio_get_all_products_and_their_versions_ref
    )
    all_tasks[all_tasks_task_reference][
        "portfolio_get_all_products_and_their_versions_ref"
    ] = portfolio_get_all_products_and_their_versions_ref
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        describe_provisioning_params_ref
    )
    all_tasks[all_tasks_task_reference][
        "describe_provisioning_params_ref"
    ] = describe_provisioning_params_ref
