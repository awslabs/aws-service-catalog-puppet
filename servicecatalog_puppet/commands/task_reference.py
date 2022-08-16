#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import copy
import json
import os
from datetime import datetime

from servicecatalog_puppet import manifest_utils, constants, yaml_utils, config
from servicecatalog_puppet.workflow import runner
from servicecatalog_puppet.workflow.dependencies import (
    get_dependencies_for_task_reference,
)
import logging
from deepmerge import always_merger

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


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
        reverse_dependencies_by_reference=list(),
        portfolio_task_reference=all_tasks_task_reference,
    )


def generate_task_reference(f):
    puppet_account_id = config.get_puppet_account_id()
    default_region = constants.HOME_REGION

    content = open(f.name, "r").read()
    manifest = manifest_utils.Manifest(yaml_utils.load(content))

    all_tasks = dict()
    tasks_by_type = dict()
    tasks_by_region = dict()
    tasks_by_account_id = dict()
    tasks_by_account_id_and_region = dict()

    #
    # First pass - handle tasks
    # First pass - create ssm output tasks
    # First pass - set up spoke local portfolios
    #
    for (
        section_name_singular,
        section_name,
    ) in constants.ALL_SECTION_NAME_SINGULAR_AND_PLURAL_LIST:
        tasks_by_type[section_name_singular] = dict()
        tasks_by_region[section_name_singular] = dict()
        tasks_by_account_id[section_name_singular] = dict()
        tasks_by_account_id_and_region[section_name_singular] = dict()
        for item_name, item in manifest.get(section_name, {}).items():
            if item.get("status") == constants.MANIFEST_STATUS_FIELD_VALUE_IGNORED:
                continue
            tasks_by_type[section_name_singular][item_name] = list()
            tasks_by_region[section_name_singular][item_name] = dict()
            tasks_by_account_id[section_name_singular][item_name] = dict()
            tasks_by_account_id_and_region[section_name_singular][item_name] = dict()
            task_reference_prefix = f"{section_name}_{item_name}"
            tasks_to_add = manifest.get_tasks_for(
                puppet_account_id, section_name, item_name
            )
            for task_to_add in tasks_to_add:
                task_to_add["section_name"] = section_name
                task_to_add["item_name"] = item_name
                # set up for later pass
                task_to_add["dependencies_by_reference"] = list()
                task_to_add["reverse_dependencies_by_reference"] = list()

                task_reference = (
                    f"{task_to_add.get('account_id')}-{task_to_add.get('region')}"
                )
                all_tasks_task_reference = f"{task_reference_prefix}_{task_reference}"
                task_to_add["task_reference"] = all_tasks_task_reference
                all_tasks[all_tasks_task_reference] = task_to_add
                tasks_by_type[section_name_singular][item_name].append(
                    all_tasks_task_reference
                )

                if not tasks_by_region[section_name_singular][item_name].get(
                    task_to_add.get("region")
                ):
                    tasks_by_region[section_name_singular][item_name][
                        task_to_add.get("region")
                    ] = list()
                tasks_by_region[section_name_singular][item_name][
                    task_to_add.get("region")
                ].append(all_tasks_task_reference)

                if not tasks_by_account_id[section_name_singular][item_name].get(
                    task_to_add.get("account_id")
                ):
                    tasks_by_account_id[section_name_singular][item_name][
                        task_to_add.get("account_id")
                    ] = list()
                tasks_by_account_id[section_name_singular][item_name][
                    task_to_add.get("account_id")
                ].append(all_tasks_task_reference)

                account_and_region = (
                    f'{task_to_add.get("account_id")}-{task_to_add.get("region")}'
                )
                if not tasks_by_account_id_and_region[section_name_singular][
                    item_name
                ].get(account_and_region):
                    tasks_by_account_id_and_region[section_name_singular][item_name][
                        account_and_region
                    ] = list()
                tasks_by_account_id_and_region[section_name_singular][item_name][
                    account_and_region
                ].append(all_tasks_task_reference)

                # ssm outputs
                # TODO add check that execution mode is spoke or hub
                # TODO add support to terminate outputs when task_to_add should be terminated
                for ssm_parameter_output in task_to_add.get("ssm_param_outputs", []):
                    output_region = ssm_parameter_output.get("region", default_region)
                    output_account_id = ssm_parameter_output.get(
                        "account_id", puppet_account_id
                    )
                    ssm_parameter_output_task_reference = f'ssm_outputs-{task_to_add.get("account_id")}-{output_region}-{ssm_parameter_output.get("param_name")}'
                    ssm_parameter_output_task_reference = ssm_parameter_output_task_reference.replace(
                        "${AWS::Region}", task_to_add.get("region")
                    ).replace(
                        "${AWS::AccountId}", task_to_add.get("account_id")
                    )
                    if all_tasks.get(ssm_parameter_output_task_reference):
                        raise Exception(
                            f"You have two tasks outputting the same SSM parameter output: {ssm_parameter_output.get('param_name')}"
                        )
                    all_tasks[ssm_parameter_output_task_reference] = dict(
                        task_reference=ssm_parameter_output_task_reference,
                        param_name=ssm_parameter_output.get("param_name")
                        .replace("${AWS::Region}", task_to_add.get("region"))
                        .replace("${AWS::AccountId}", task_to_add.get("account_id")),
                        stack_output=ssm_parameter_output.get("stack_output"),
                        force_operation=ssm_parameter_output.get(
                            "force_operation", False
                        ),
                        account_id=output_account_id,
                        region=output_region,
                        dependencies_by_reference=[all_tasks_task_reference],
                        reverse_dependencies_by_reference=list(),
                        task_generating_output=all_tasks_task_reference,
                        section_name="ssm_outputs",
                    )

                if section_name == constants.LAUNCHES:
                    handle_launches(
                        all_tasks,
                        all_tasks_task_reference,
                        item_name,
                        puppet_account_id,
                        section_name,
                        task_reference,
                        task_to_add,
                    )

                if section_name == constants.SPOKE_LOCAL_PORTFOLIOS:
                    handle_spoke_local_portfolios(
                        all_tasks,
                        all_tasks_task_reference,
                        item_name,
                        puppet_account_id,
                        section_name,
                        task_reference,
                        task_to_add,
                    )

                if section_name == constants.WORKSPACES:
                    handle_workspaces(
                        all_tasks,
                        all_tasks_task_reference,
                        item_name,
                        puppet_account_id,
                        section_name,
                        task_reference,
                        task_to_add,
                    )

    #
    # Second pass - adding get parameters
    #
    # TODO handle boto3 parameters
    new_tasks = dict()
    for task_reference, task in all_tasks.items():
        parameters = dict()
        launch_parameters = (
            manifest.get(task.get("section_name"), {})
            .get(task.get("item_name"), {})
            .get("parameters", {})
        )
        manifest_parameters = manifest.get("parameters")
        account_parameters = manifest.get_account(task.get("account_id")).get(
            "parameters"
        )

        always_merger.merge(parameters, manifest_parameters)
        always_merger.merge(parameters, launch_parameters)
        always_merger.merge(parameters, account_parameters)

        for parameter_name, parameter_details in parameters.items():
            if parameter_details.get("ssm"):
                ssm_parameter_details = parameter_details.get("ssm")
                interpolation_output_account = task.get("account_id")
                interpolation_output_region = task.get("region")
                owning_account = ssm_parameter_details.get(
                    "account_id", puppet_account_id
                )
                owning_region = ssm_parameter_details.get("region", default_region)
                task_reference = f"{owning_account}-{owning_region}"
                param_name = (
                    ssm_parameter_details.get("name")
                    .replace("${AWS::Region}", interpolation_output_region)
                    .replace("${AWS::AccountId}", interpolation_output_account)
                )
                ssm_parameter_task_reference = (
                    f"ssm_parameters-{task_reference}-{param_name}"
                )
                if all_tasks.get(
                    ssm_parameter_task_reference.replace(
                        "ssm_parameters-", "ssm_outputs-"
                    )
                ):
                    dependency = [
                        ssm_parameter_task_reference.replace(
                            "ssm_parameters-", "ssm_outputs-"
                        )
                    ]
                else:
                    dependency = []
                new_tasks[ssm_parameter_task_reference] = dict(
                    task_reference=ssm_parameter_task_reference,
                    account_id=owning_account,
                    region=owning_region,
                    param_name=param_name,
                    dependencies_by_reference=dependency,
                    reverse_dependencies_by_reference=list(),
                    section_name="ssm_parameters",
                )
                task["dependencies_by_reference"].append(ssm_parameter_task_reference)
    all_tasks.update(new_tasks)

    #
    # Third pass - replacing dependencies with dependencies_by_reference
    #
    for task_reference, task in all_tasks.items():

        for dependency in task.get("dependencies", []):
            section = dependency.get("type")
            affinity = dependency.get("affinity")
            name = dependency.get("name")

            if affinity == section:
                if not tasks_by_type[section].get(name):
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of {affinity} affinity - {name} is not deployed"
                    )
                task["dependencies_by_reference"].extend(tasks_by_type[section][name])

            if affinity == constants.AFFINITY_REGION:
                if not tasks_by_region[section][name].get(task.get("region")):
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of region affinity - {name} is not deployed in the region: {task.get('region')}"
                    )
                task["dependencies_by_reference"].extend(
                    tasks_by_region[section][name][task.get("region")]
                )

            if affinity == constants.AFFINITY_ACCOUNT:
                if not tasks_by_account_id[section][name].get(task.get("account_id")):
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of account affinity - {name} is not deployed in the account_id: {task.get('account_id')}"
                    )
                task["dependencies_by_reference"].extend(
                    tasks_by_account_id[section][name][task.get("account_id")]
                )

            if affinity == constants.AFFINITY_ACCOUNT_AND_REGION:
                account_and_region = f"{task.get('account_id')}-{task.get('region')}"
                if not tasks_by_account_id_and_region[section][name].get(
                    account_and_region
                ):
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of account-and-region affinity - {name} is not deployed in the account_id and region: {account_and_region}"
                    )
                task["dependencies_by_reference"].extend(
                    tasks_by_account_id_and_region[section][name][account_and_region]
                )

        for dep in task["dependencies_by_reference"]:
            all_tasks[dep]["reverse_dependencies_by_reference"].append(task_reference)

    reference = dict(
        all_tasks=all_tasks,
        # tasks_by_type=tasks_by_type,
    )
    open(f.name.replace("-expanded", "-task-reference"), "w").write(
        yaml_utils.dump(reference)
    )


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
            dependencies_by_reference=[],
            reverse_dependencies_by_reference=[],
            account_id=task_to_add.get("account_id"),
            section_name=constants.WORKSPACE_ACCOUNT_PREPARATION,
        )
    if workspace_account_preparation_ref not in all_tasks[all_tasks_task_reference].get(
        "dependencies_by_reference"
    ):
        all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
            workspace_account_preparation_ref
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
            all_tasks[ref] = dict(
                status=task_to_add.get("status"),
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                execution=task_to_add.get("execution"),
                dependencies_by_reference=[],
                reverse_dependencies_by_reference=list(),
                task_reference=ref,
                spoke_local_portfolio_name=item_name,
                section_name=constants.PORTFOLIO_ASSOCIATIONS,
                associations=task_to_add.get("associations"),
            )
        # DELETE THE LAUNCH CONSTRAINTS IF IT EXISTS
        if task_to_add.get("launch_constraints"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"launch_constraints-{shared_ref}"
            deps.append(ref)
            all_tasks[ref] = dict(
                status=task_to_add.get("status"),
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                execution=task_to_add.get("execution"),
                dependencies_by_reference=[],
                reverse_dependencies_by_reference=list(),
                task_reference=ref,
                section_name=constants.PORTFOLIO_CONSTRAINTS_LAUNCH,
                spoke_local_portfolio_name=item_name,
                launch_constraints=task_to_add["launch_constraints"],
            )
        # DELETE THE RESOURCE UPDATE CONSTRAINTS IF IT EXISTS
        if task_to_add.get("resource_update_constraints"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"resource_update_constraints-{shared_ref}"
            deps.append(ref)
            all_tasks[ref] = dict(
                status=task_to_add.get("status"),
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                execution=task_to_add.get("execution"),
                dependencies_by_reference=[],
                reverse_dependencies_by_reference=list(),
                task_reference=ref,
                section_name=constants.PORTFOLIO_CONSTRAINTS_RESOURCE_UPDATE,
                spoke_local_portfolio_name=item_name,
                resource_update_constraints=task_to_add["resource_update_constraints"],
            )
        # GET THE SPOKE LOCAL PORTFOLIO SO WE CAN DELETE THE ASSOCIATIONS
        spoke_portfolio_ref = f"{constants.PORTFOLIO_LOCAL}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        all_tasks[spoke_portfolio_ref] = dict(
            puppet_account_id=puppet_account_id,
            task_reference=spoke_portfolio_ref,
            dependencies_by_reference=[],
            reverse_dependencies_by_reference=[],
            account_id=task_to_add.get("account_id"),
            region=task_to_add.get("region"),
            portfolio=task_to_add.get("portfolio"),
            status=task_to_add.get("status"),
            section_name=constants.PORTFOLIO_LOCAL,
        )

        if not is_sharing_with_puppet_account:
            # GET THE SPOKE PRODUCTS AND VERSIONS SO WE CAN DISASSOCIATE THEM
            spoke_portfolio_all_products_and_versions_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[spoke_portfolio_all_products_and_versions_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=spoke_portfolio_all_products_and_versions_ref,
                dependencies_by_reference=[spoke_portfolio_ref],
                reverse_dependencies_by_reference=[],
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                portfolio_task_reference=spoke_portfolio_ref,
                section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
            )

            disassociate_portfolio_all_products_and_versions_ref = f"{constants.PORTFOLIO_DISASSOCIATE_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[disassociate_portfolio_all_products_and_versions_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=disassociate_portfolio_all_products_and_versions_ref,
                dependencies_by_reference=[
                    spoke_portfolio_all_products_and_versions_ref,
                    spoke_portfolio_ref,
                ],
                reverse_dependencies_by_reference=[],
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                portfolio_task_reference=spoke_portfolio_ref,
                section_name=constants.PORTFOLIO_DISASSOCIATE_ALL_PRODUCTS_AND_THEIR_VERSIONS,
            )
            deps.append(disassociate_portfolio_all_products_and_versions_ref)

        # DELETE THE SPOKE LOCAL PORTFOLIO ASSOCIATION
        spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        all_tasks[spoke_portfolio_puppet_association_ref] = dict(
            status=task_to_add.get("status"),
            puppet_account_id=puppet_account_id,
            task_reference=spoke_portfolio_puppet_association_ref,
            portfolio_task_reference=spoke_portfolio_ref,
            dependencies_by_reference=[spoke_portfolio_ref],
            reverse_dependencies_by_reference=[],
            account_id=task_to_add.get("account_id"),
            region=task_to_add.get("region"),
            portfolio=task_to_add.get("portfolio"),
            section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
        )
        deps.append(spoke_portfolio_puppet_association_ref)

        task_to_add["dependencies_by_reference"].extend(deps)

    else:
        dependencies_for_constraints = list()
        if is_sharing_with_puppet_account:
            # CREATE SPOKE ASSOCIATIONS
            spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[spoke_portfolio_puppet_association_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=spoke_portfolio_puppet_association_ref,
                portfolio_task_reference=all_tasks_task_reference,
                dependencies_by_reference=[all_tasks_task_reference],
                reverse_dependencies_by_reference=[],
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
            )

            # GET THE SPOKE PRODUCTS AND VERSIONS - USE THE AFTER ONE AS NO PRODUCTS WILL BE COPIED WHEN SHARING WITH PUPPET ACCOUNT
            spoke_portfolio_all_products_and_versions_after_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-after-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[spoke_portfolio_all_products_and_versions_after_ref] = dict(
                **get_spoke_local_portfolio_common_args(
                    task_to_add,
                    all_tasks_task_reference,
                    [spoke_portfolio_puppet_association_ref],
                ),
                task_reference=spoke_portfolio_all_products_and_versions_after_ref,
                section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
            )
            dependencies_for_constraints.append(
                spoke_portfolio_all_products_and_versions_after_ref
            )

        else:
            # GET THE HUB PORTFOLIO
            hub_portfolio_ref = f"{constants.PORTFOLIO_LOCAL}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[hub_portfolio_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=hub_portfolio_ref,
                dependencies_by_reference=[],
                reverse_dependencies_by_reference=[],
                account_id=puppet_account_id,
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                status=task_to_add.get("status"),
                section_name=constants.PORTFOLIO_LOCAL,
            )
            all_tasks[all_tasks_task_reference][
                "portfolio_task_reference"
            ] = hub_portfolio_ref
            all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
                hub_portfolio_ref
            )

            # CREATE THE HUB ASSOCIATIONS
            hub_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[hub_portfolio_puppet_association_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=hub_portfolio_puppet_association_ref,
                portfolio_task_reference=hub_portfolio_ref,
                dependencies_by_reference=[hub_portfolio_ref],
                reverse_dependencies_by_reference=[],
                account_id=puppet_account_id,
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,  # TODO test in with a new spoke local
            )

            # SHARE THE PORTFOLIO
            share_and_accept_ref = f"portfolio_share_and_accept-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"  # TODO need to rename to avoid duplicates
            sharing_mode = task_to_add.get(
                "sharing_mode", constants.SHARING_MODE_ACCOUNT
            )  # TODO need to make sure global sharing cascades into the expanded manifest file
            # TODO handle when account_id == puppet_account_id
            all_tasks[share_and_accept_ref] = dict(
                puppet_account_id=puppet_account_id,
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                task_reference=share_and_accept_ref,
                dependencies_by_reference=[hub_portfolio_ref],
                reverse_dependencies_by_reference=[],
                portfolio=task_to_add.get("portfolio"),
                portfolio_task_reference=hub_portfolio_ref,
                section_name=f"portfolio-share-and-accept-{sharing_mode.lower()}",
            )

            # GET THE HUB PRODUCTS AND VERSIONS SO WE KNOW WHAT NEEDS TO BE COPIED OR IMPORTED
            hub_portfolio_all_products_and_versions_before_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-before-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[hub_portfolio_all_products_and_versions_before_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=hub_portfolio_all_products_and_versions_before_ref,
                dependencies_by_reference=[
                    hub_portfolio_ref,
                    hub_portfolio_puppet_association_ref,  # TODO reduce this down to one ?
                ],
                portfolio_task_reference=hub_portfolio_ref,
                reverse_dependencies_by_reference=[],
                account_id=puppet_account_id,  # EPF changed
                region=task_to_add.get("region"),
                section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
            )

            # CREATE SPOKE ASSOCIATIONS
            spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[spoke_portfolio_puppet_association_ref] = dict(
                puppet_account_id=puppet_account_id,
                task_reference=spoke_portfolio_puppet_association_ref,
                portfolio_task_reference=all_tasks_task_reference,
                dependencies_by_reference=[all_tasks_task_reference],
                reverse_dependencies_by_reference=[],
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                portfolio=task_to_add.get("portfolio"),
                section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
            )

            # GET THE SPOKE PRODUCTS AND VERSIONS SO WE KNOW WHAT IS MISSING OR NEEDS UPDATING
            spoke_portfolio_all_products_and_versions_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[spoke_portfolio_all_products_and_versions_ref] = dict(
                **get_spoke_local_portfolio_common_args(
                    task_to_add,
                    all_tasks_task_reference,
                    [spoke_portfolio_puppet_association_ref],
                ),
                task_reference=spoke_portfolio_all_products_and_versions_ref,
                section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
            )

            # COPY OR IMPORT THE CHANGES BETWEEN THE TWO PORTFOLIOS
            product_generation_method = task_to_add.get("product_generation_method")
            portfolio_import_or_copy_ref = f"portfolio_{product_generation_method}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            all_tasks[portfolio_import_or_copy_ref] = dict(
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
            )
            dependencies_for_constraints.append(portfolio_import_or_copy_ref)

        if task_to_add.get("associations"):
            shared_ref = f"{section_name}-{item_name}-{task_to_add.get('account_id')}-{task_to_add.get('region')}"
            ref = f"portfolio_associations-{shared_ref}"
            all_tasks[ref] = dict(
                **get_spoke_local_portfolio_common_args(
                    task_to_add, all_tasks_task_reference
                ),
                task_reference=ref,
                spoke_local_portfolio_name=item_name,
                section_name=constants.PORTFOLIO_ASSOCIATIONS,
                associations=task_to_add.get("associations"),
            )
        if not is_sharing_with_puppet_account:
            # GET NEW PRODUCT AND VERSIONS FOLLOWING THE IMPORT OR COPY
            spoke_portfolio_all_products_and_versions_after_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-after-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
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
            )
            dependencies_for_constraints.append(
                spoke_portfolio_all_products_and_versions_after_ref
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
            )


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
    all_tasks[hub_portfolio_ref] = dict(
        puppet_account_id=puppet_account_id,
        task_reference=hub_portfolio_ref,
        dependencies_by_reference=[],
        reverse_dependencies_by_reference=[],
        account_id=puppet_account_id,
        region=task_to_add.get("region"),
        portfolio=task_to_add.get("portfolio"),
        status=task_to_add.get("status"),
        section_name=constants.PORTFOLIO_LOCAL,
    )

    spoke_portfolio_puppet_association_ref = None
    if is_deploying_into_puppet_account:
        portfolio_deploying_from = hub_portfolio_ref
    else:
        # share the portfolio and accept it
        share_and_accept_ref = f"portfolio_share_and_accept-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"  # TODO need to rename to avoid duplicates
        sharing_mode = task_to_add.get(
            "sharing_mode", constants.SHARING_MODE_ACCOUNT
        )  # TODO need to make sure global sharing cascades into the expanded manifest file
        # TODO handle when account_id == puppet_account_id
        all_tasks[share_and_accept_ref] = dict(
            puppet_account_id=puppet_account_id,
            account_id=task_to_add.get("account_id"),
            region=task_to_add.get("region"),
            task_reference=share_and_accept_ref,
            dependencies_by_reference=[hub_portfolio_ref],
            reverse_dependencies_by_reference=[],
            portfolio=task_to_add.get("portfolio"),
            portfolio_task_reference=hub_portfolio_ref,
            section_name=f"portfolio-share-and-accept-{sharing_mode.lower()}",
        )

        # GET THE IMPORTED PORTFOLIO
        spoke_portfolio_ref = f"{constants.PORTFOLIO_IMPORTED}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        all_tasks[spoke_portfolio_ref] = dict(
            puppet_account_id=puppet_account_id,
            task_reference=spoke_portfolio_ref,
            dependencies_by_reference=[share_and_accept_ref],
            reverse_dependencies_by_reference=[],
            account_id=task_to_add.get("account_id"),
            region=task_to_add.get("region"),
            portfolio=task_to_add.get("portfolio"),
            sharing_mode=task_to_add.get(
                "sharing_mode", constants.SHARING_MODE_ACCOUNT
            ),  # TODO verify
            section_name=constants.PORTFOLIO_IMPORTED,
        )
        portfolio_deploying_from = spoke_portfolio_ref

        spoke_portfolio_puppet_association_ref = f"{constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION}-{task_to_add.get('account_id')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        all_tasks[spoke_portfolio_puppet_association_ref] = dict(
            puppet_account_id=puppet_account_id,
            task_reference=spoke_portfolio_puppet_association_ref,
            portfolio_task_reference=spoke_portfolio_ref,
            dependencies_by_reference=[spoke_portfolio_ref],
            reverse_dependencies_by_reference=[],
            account_id=task_to_add.get("account_id"),
            region=task_to_add.get("region"),
            portfolio=task_to_add.get("portfolio"),
            section_name=constants.PORTFOLIO_PUPPET_ROLE_ASSOCIATION,
        )
        all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
            spoke_portfolio_puppet_association_ref
        )

    # GET the provisioning parameters
    describe_provisioning_params_ref = f"{constants.DESCRIBE_PROVISIONING_PARAMETERS}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}-{task_to_add.get('product')}-{task_to_add.get('version')}"
    all_tasks[describe_provisioning_params_ref] = dict(
        puppet_account_id=puppet_account_id,
        task_reference=describe_provisioning_params_ref,
        dependencies_by_reference=[
            portfolio_deploying_from
        ],  # associations are added here and so this is a dependency
        reverse_dependencies_by_reference=[],
        account_id=puppet_account_id,
        region=task_to_add.get("region"),
        portfolio=task_to_add.get("portfolio"),
        product=task_to_add.get("product"),
        version=task_to_add.get("version"),
        section_name=constants.DESCRIBE_PROVISIONING_PARAMETERS,
    )

    # GET all the products for the spoke
    if spoke_portfolio_puppet_association_ref is None:
        deps = [portfolio_deploying_from]
    else:
        deps = [portfolio_deploying_from, spoke_portfolio_puppet_association_ref]
    portfolio_get_all_products_and_their_versions_ref = f"{constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS}-{puppet_account_id}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
    all_tasks[portfolio_get_all_products_and_their_versions_ref] = dict(
        puppet_account_id=puppet_account_id,
        task_reference=portfolio_get_all_products_and_their_versions_ref,
        dependencies_by_reference=deps,
        portfolio_task_reference=portfolio_deploying_from,
        reverse_dependencies_by_reference=[],
        account_id=puppet_account_id,
        region=task_to_add.get("region"),
        section_name=constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS,
    )

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


def deploy_from_task_reference(f, num_workers):
    puppet_account_id = config.get_puppet_account_id()

    tasks_to_run = list()
    reference = yaml_utils.load(open(f.name, "r").read())
    all_tasks = reference.get("all_tasks")

    for task_reference, task in all_tasks.items():
        tasks_to_run.append(
            get_dependencies_for_task_reference.create(
                manifest_task_reference_file_path=f.name,
                puppet_account_id=puppet_account_id,
                parameters_to_use=task,
            )
        )

    puppet_account_id = config.get_puppet_account_id()
    executor_account_id = puppet_account_id
    is_dry_run = False
    is_list_launches = False
    execution_mode = constants.EXECUTION_MODE_HUB
    on_complete_url = None
    running_exploded = False
    output_cache_starting_point = ""
    single_account = ""

    if os.environ.get("SCT_CACHE_INVALIDATOR"):
        logger.info(
            f"Found existing SCT_CACHE_INVALIDATOR: {os.environ.get('SCT_CACHE_INVALIDATOR')}"
        )
    else:
        os.environ["SCT_CACHE_INVALIDATOR"] = str(datetime.now())

    os.environ["SCT_EXECUTION_MODE"] = str(execution_mode)
    os.environ["SCT_SINGLE_ACCOUNT"] = str(single_account)
    os.environ["SCT_IS_DRY_RUN"] = str(is_dry_run)
    os.environ["EXECUTOR_ACCOUNT_ID"] = str(executor_account_id)
    os.environ["SCT_SHOULD_USE_SNS"] = str(config.get_should_use_sns(puppet_account_id))
    os.environ["SCT_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS"] = str(
        config.get_should_delete_rollback_complete_stacks(puppet_account_id)
    )
    os.environ["SCT_SHOULD_USE_PRODUCT_PLANS"] = str(
        config.get_should_use_product_plans(
            puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
        )
    )
    os.environ["SCT_INITIALISER_STACK_TAGS"] = json.dumps(
        config.get_initialiser_stack_tags()
    )

    runner.run_tasks(
        puppet_account_id,
        executor_account_id,
        tasks_to_run,
        num_workers,
        is_dry_run,
        is_list_launches,
        execution_mode,
        on_complete_url,
        running_exploded,
        output_cache_starting_point=output_cache_starting_point,
    )
