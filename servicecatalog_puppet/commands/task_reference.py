#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import copy
import logging
import os
import pathlib

from deepmerge import always_merger

from servicecatalog_puppet import manifest_utils, constants, serialisation_utils, config
from servicecatalog_puppet.commands import graph
from servicecatalog_puppet.workflow import runner
from servicecatalog_puppet.workflow.dependencies import (
    task_factory,
    resources_factory,
)
import networkx as nx

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
        portfolio_task_reference=all_tasks_task_reference,
    )


def ensure_no_cyclic_dependencies(name, tasks):
    g = nx.DiGraph()
    for t_name, t in tasks.items():
        uid = t_name
        data = t
        g.add_nodes_from(
            [(uid, data),]
        )
        for duid in t.get("dependencies_by_reference", []):
            g.add_edge(uid, duid)
    try:
        cycle = nx.find_cycle(g)
        raise Exception(
            f"found cyclic dependency task reference file {name} between: {cycle}"
        )
    except nx.exception.NetworkXNoCycle:
        pass


def generate_complete_task_reference(puppet_account_id, manifest, output_file_path):
    default_region = config.get_home_region(puppet_account_id)
    regions_in_use = config.get_regions()

    all_tasks = dict()
    tasks_by_type = dict()
    tasks_by_region = dict()
    tasks_by_account_id = dict()
    tasks_by_account_id_and_region = dict()

    #
    # ZERO pass - generate policies
    #
    organizations_to_share_with = dict()
    ous_to_share_with = dict()
    accounts_to_share_with = dict()
    for a in manifest.get("accounts", []):
        if a.get("organization"):
            organizations_to_share_with[a.get("organization")] = True
        if a.get("expanded_from"):
            ous_to_share_with[a.get("expanded_from")] = True
        else:
            accounts_to_share_with[a.get("account_id")] = True

    all_tasks[constants.CREATE_POLICIES] = dict(
        execution=constants.EXECUTION_MODE_HUB,
        manifest_section_names=dict(),
        manifest_item_names=dict(),
        account_id=puppet_account_id,
        region=default_region,
        manifest_account_ids=dict(),
        task_reference=constants.CREATE_POLICIES,
        dependencies_by_reference=list(),
        section_name=constants.CREATE_POLICIES,
        organizations_to_share_with=list(organizations_to_share_with.keys()),
        ous_to_share_with=list(ous_to_share_with.keys()),
        accounts_to_share_with=list(accounts_to_share_with.keys()),
    )

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
            tasks_by_type[section_name_singular][item_name] = list()
            tasks_by_region[section_name_singular][item_name] = dict()
            tasks_by_account_id[section_name_singular][item_name] = dict()
            tasks_by_account_id_and_region[section_name_singular][item_name] = dict()
            task_reference_prefix = f"{section_name}_{item_name}"
            tasks_to_add = manifest.get_tasks_for(
                puppet_account_id,
                section_name,
                item_name,
                default_region,
                regions_in_use,
            )
            for task_to_add in tasks_to_add:
                task_to_add["manifest_section_names"] = {section_name: True}
                task_to_add["manifest_item_names"] = {item_name: True}
                task_to_add["manifest_account_ids"] = {
                    task_to_add.get("account_id"): True
                }
                task_to_add["section_name"] = section_name
                task_to_add["item_name"] = item_name
                # set up for later pass
                task_to_add["dependencies_by_reference"] = [constants.CREATE_POLICIES]

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
                for ssm_parameter_output in task_to_add.get("ssm_param_outputs", []):
                    output_region = ssm_parameter_output.get("region", default_region)
                    output_account_id = ssm_parameter_output.get(
                        "account_id", puppet_account_id
                    )
                    ssm_parameter_output_task_reference = f'{constants.SSM_OUTPUTS}-{task_to_add.get("account_id")}-{output_region}-{ssm_parameter_output.get("param_name")}'
                    ssm_parameter_output_task_reference = ssm_parameter_output_task_reference.replace(
                        "${AWS::Region}", task_to_add.get("region")
                    ).replace(
                        "${AWS::AccountId}", task_to_add.get("account_id")
                    )
                    if all_tasks.get(ssm_parameter_output_task_reference):
                        raise Exception(
                            f"You have two tasks outputting the same SSM parameter output: {ssm_parameter_output.get('param_name')}"
                        )

                    else:
                        all_tasks[ssm_parameter_output_task_reference] = dict(
                            manifest_section_names=dict(),
                            manifest_item_names=dict(),
                            manifest_account_ids=dict(),
                            task_reference=ssm_parameter_output_task_reference,
                            param_name=ssm_parameter_output.get("param_name")
                            .replace("${AWS::Region}", task_to_add.get("region"))
                            .replace(
                                "${AWS::AccountId}", task_to_add.get("account_id")
                            ),
                            stack_output=ssm_parameter_output.get("stack_output"),
                            force_operation=ssm_parameter_output.get(
                                "force_operation", False
                            ),
                            account_id=output_account_id,
                            region=output_region,
                            dependencies_by_reference=[all_tasks_task_reference],
                            task_generating_output=all_tasks_task_reference,
                            status=task_to_add.get("status"),
                            section_name=constants.SSM_OUTPUTS,
                        )
                    all_tasks[ssm_parameter_output_task_reference][
                        "manifest_section_names"
                    ][section_name] = True
                    all_tasks[ssm_parameter_output_task_reference][
                        "manifest_item_names"
                    ][item_name] = True
                    all_tasks[ssm_parameter_output_task_reference][
                        "manifest_account_ids"
                    ][task_to_add.get("account_id")] = True

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

                if section_name == constants.STACKS:
                    handle_stacks(
                        all_tasks,
                        all_tasks_task_reference,
                        item_name,
                        puppet_account_id,
                        section_name,
                        task_reference,
                        task_to_add,
                    )

                if section_name == constants.SERVICE_CONTROL_POLICIES:
                    handle_service_control_policies(
                        all_tasks,
                        all_tasks_task_reference,
                        item_name,
                        puppet_account_id,
                        section_name,
                        task_reference,
                        task_to_add,
                    )

                if section_name == constants.TAG_POLICIES:
                    handle_tag_policies(
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
    new_tasks = dict()
    for task_reference, task in all_tasks.items():
        parameters = {}
        launch_parameters = (
            manifest.get(task.get("section_name"), {})
            .get(task.get("item_name"), {})
            .get("parameters", {})
        )
        manifest_parameters = copy.deepcopy(manifest.get("parameters"))
        account_parameters = manifest.get_parameters_for_account(task.get("account_id"))

        always_merger.merge(parameters, manifest_parameters)
        always_merger.merge(parameters, launch_parameters)
        always_merger.merge(parameters, account_parameters)

        if task.get("status") != constants.TERMINATED:
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

                    task_def = dict(
                        account_id=owning_account,
                        region=owning_region,
                        manifest_section_names=dict(
                            **task.get("manifest_section_names")
                        ),
                        manifest_item_names=dict(**task.get("manifest_item_names")),
                        manifest_account_ids=dict(**task.get("manifest_account_ids")),
                    )
                    path = ssm_parameter_details.get("path")
                    if path is None:
                        ssm_parameter_task_reference = (
                            f"{constants.SSM_PARAMETERS}-{task_reference}-{param_name}"
                        )
                        task_def["param_name"] = param_name
                        task_def["section_name"] = constants.SSM_PARAMETERS
                    else:
                        ssm_parameter_task_reference = f"{constants.SSM_PARAMETERS_WITH_A_PATH}-{task_reference}-{path}"
                        task_def["path"] = path
                        task_def["section_name"] = constants.SSM_PARAMETERS_WITH_A_PATH
                    task_def["task_reference"] = ssm_parameter_task_reference

                    potential_output_task_ref = f"{constants.SSM_PARAMETERS}-{task_reference}-{param_name}".replace(
                        f"{constants.SSM_PARAMETERS}-", f"{constants.SSM_OUTPUTS}-"
                    )
                    if all_tasks.get(potential_output_task_ref):
                        dependency = [potential_output_task_ref]
                    else:
                        dependency = []
                    task_def["dependencies_by_reference"] = dependency

                    # IF THERE ARE TWO TASKS USING THE SAME PARAMETER AND THE OTHER TASK ADDED IT FIRST
                    if new_tasks.get(ssm_parameter_task_reference):
                        existing_task_def = new_tasks[ssm_parameter_task_reference]
                        # AVOID DUPLICATE DEPENDENCIES IN THE SAME LIST
                        for dep in dependency:
                            if (
                                dep
                                not in existing_task_def["dependencies_by_reference"]
                            ):
                                existing_task_def["dependencies_by_reference"].append(
                                    dep
                                )
                    else:
                        new_tasks[ssm_parameter_task_reference] = task_def

                    new_tasks[ssm_parameter_task_reference][
                        "manifest_section_names"
                    ].update(task.get("manifest_section_names"))
                    new_tasks[ssm_parameter_task_reference][
                        "manifest_item_names"
                    ].update(task.get("manifest_item_names"))
                    new_tasks[ssm_parameter_task_reference][
                        "manifest_account_ids"
                    ].update(task.get("manifest_account_ids"))

                    task["dependencies_by_reference"].append(
                        ssm_parameter_task_reference
                    )
                # HANDLE BOTO3 PARAMS
                if parameter_details.get("boto3"):
                    boto3_parameter_details = parameter_details.get("boto3")
                    account_id_to_use_for_boto3_call = (
                        str(
                            boto3_parameter_details.get("account_id", puppet_account_id)
                        )
                        .replace("${AWS::AccountId}", task.get("account_id"))
                        .replace("${AWS::PuppetAccountId}", puppet_account_id)
                    )
                    region_to_use_for_boto3_call = boto3_parameter_details.get(
                        "region", constants.HOME_REGION
                    ).replace("${AWS::Region}", task.get("region"))

                    dependencies = list()
                    if parameter_details.get("cloudformation_stack_output"):
                        cloudformation_stack_output = parameter_details[
                            "cloudformation_stack_output"
                        ]
                        stack_ref_account_id = (
                            str(cloudformation_stack_output.get("account_id"))
                            .replace("${AWS::AccountId}", task.get("account_id"))
                            .replace("${AWS::PuppetAccountId}", puppet_account_id)
                        )
                        stack_ref_region = cloudformation_stack_output.get(
                            "region"
                        ).replace("${AWS::Region}", task.get("region"))
                        stack_ref_stack = cloudformation_stack_output.get("stack_name")
                        stack_ref = f"{constants.STACKS}_{stack_ref_stack}_{stack_ref_account_id}-{stack_ref_region}"
                        if all_tasks.get(stack_ref):
                            dependencies.append(stack_ref)
                        section_name_to_use = constants.STACKS
                        item_name_to_use = stack_ref_stack

                    boto3_parameter_task_reference = f"{constants.BOTO3_PARAMETERS}-{section_name_to_use}-{item_name_to_use}-{parameter_name}-{account_id_to_use_for_boto3_call}-{region_to_use_for_boto3_call}"
                    if not new_tasks.get(boto3_parameter_task_reference):
                        new_tasks[boto3_parameter_task_reference] = dict(
                            status=task.get("status"),
                            task_reference=boto3_parameter_task_reference,
                            dependencies_by_reference=dependencies,
                            manifest_section_names=dict(),
                            manifest_item_names=dict(),
                            manifest_account_ids=dict(),
                            account_id=account_id_to_use_for_boto3_call,
                            region=region_to_use_for_boto3_call,
                            arguments=boto3_parameter_details.get("arguments"),
                            call=boto3_parameter_details.get("call"),
                            client=boto3_parameter_details.get("client"),
                            filter=boto3_parameter_details.get("filter"),
                            use_paginator=boto3_parameter_details.get("use_paginator"),
                            section_name=constants.BOTO3_PARAMETERS,
                        )

                    new_tasks[boto3_parameter_task_reference][
                        "manifest_section_names"
                    ].update(task.get("manifest_section_names"))
                    new_tasks[boto3_parameter_task_reference][
                        "manifest_item_names"
                    ].update(task.get("manifest_item_names"))
                    new_tasks[boto3_parameter_task_reference][
                        "manifest_account_ids"
                    ].update(task.get("manifest_account_ids"))

                    task["dependencies_by_reference"].append(
                        boto3_parameter_task_reference
                    )

    all_tasks.update(new_tasks)

    #
    # Third pass - replacing dependencies with dependencies_by_reference and adding resources
    #
    for task_reference, task in all_tasks.items():
        for dependency in task.get("dependencies", []):
            section = dependency.get("type")
            affinity = dependency.get("affinity")
            name = dependency.get("name")

            if affinity == section:
                if tasks_by_type[section].get(name):
                    task["dependencies_by_reference"].extend(
                        tasks_by_type[section][name]
                    )
                else:
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of {affinity} affinity - {name} is not deployed for task {task_reference}"
                    )

            if affinity == constants.AFFINITY_REGION:
                if tasks_by_region[section][name].get(task.get("region")):
                    task["dependencies_by_reference"].extend(
                        tasks_by_region[section][name][task.get("region")]
                    )
                else:
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of region affinity - {name} is not deployed in the region: {task.get('region')} for task {task_reference}"
                    )

            if affinity == constants.AFFINITY_ACCOUNT:
                if tasks_by_account_id[section][name].get(task.get("account_id")):
                    task["dependencies_by_reference"].extend(
                        tasks_by_account_id[section][name][task.get("account_id")]
                    )
                else:
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of account affinity - {name} is not deployed in the account_id: {task.get('account_id')} for task {task_reference}"
                    )

            if affinity == constants.AFFINITY_ACCOUNT_AND_REGION:
                account_and_region = f"{task.get('account_id')}-{task.get('region')}"
                if tasks_by_account_id_and_region[section][name].get(
                    account_and_region
                ):
                    task["dependencies_by_reference"].extend(
                        tasks_by_account_id_and_region[section][name][
                            account_and_region
                        ]
                    )
                else:
                    # TODO should this be a warning or an error
                    raise Exception(
                        f"invalid use of account-and-region affinity - {name} is not deployed in the account_id and region: {account_and_region} for task {task_reference}"
                    )
        resources = resources_factory.create(
            task.get("section_name"), task, puppet_account_id
        )
        task["resources_required"] = resources

    reference = dict(all_tasks=all_tasks,)
    ensure_no_cyclic_dependencies("complete task reference", all_tasks)
    open(output_file_path, "w").write(serialisation_utils.dump_as_json(reference))
    return reference


def handle_service_control_policies(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    get_or_create_policy_ref = (
        f"{constants.GET_OR_CREATE_SERVICE_CONTROL_POLICIES_POLICY}-{item_name}"
    )
    if not all_tasks.get(get_or_create_policy_ref):
        all_tasks[get_or_create_policy_ref] = dict(
            task_reference=get_or_create_policy_ref,
            execution="hub",
            account_id=puppet_account_id,
            region=task_to_add.get("region"),
            policy_name=task_to_add.get("service_control_policy_name"),
            policy_description=task_to_add.get("description"),
            policy_content=task_to_add.get("content"),
            dependencies_by_reference=list(),
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
            section_name=constants.GET_OR_CREATE_SERVICE_CONTROL_POLICIES_POLICY,
        )
        all_tasks[all_tasks_task_reference][
            "get_or_create_policy_ref"
        ] = get_or_create_policy_ref
        all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
            get_or_create_policy_ref
        )
        all_tasks[get_or_create_policy_ref]["manifest_section_names"].update(
            task_to_add.get("manifest_section_names")
        )
        all_tasks[get_or_create_policy_ref]["manifest_item_names"].update(
            task_to_add.get("manifest_item_names")
        )
        all_tasks[get_or_create_policy_ref]["manifest_account_ids"].update(
            task_to_add.get("manifest_account_ids")
        )


def handle_tag_policies(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    get_or_create_policy_ref = (
        f"{constants.GET_OR_CREATE_TAG_POLICIES_POLICY}-{item_name}"
    )
    if not all_tasks.get(get_or_create_policy_ref):
        all_tasks[get_or_create_policy_ref] = dict(
            task_reference=get_or_create_policy_ref,
            execution="hub",
            account_id=puppet_account_id,
            region=task_to_add.get("region"),
            policy_name=task_to_add.get("tag_policy_name"),
            policy_description=task_to_add.get("description"),
            policy_content=task_to_add.get("content"),
            dependencies_by_reference=list(),
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
            section_name=constants.GET_OR_CREATE_TAG_POLICIES_POLICY,
        )
        all_tasks[all_tasks_task_reference][
            "get_or_create_policy_ref"
        ] = get_or_create_policy_ref
        all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
            get_or_create_policy_ref
        )
        all_tasks[get_or_create_policy_ref]["manifest_section_names"].update(
            task_to_add.get("manifest_section_names")
        )
        all_tasks[get_or_create_policy_ref]["manifest_item_names"].update(
            task_to_add.get("manifest_item_names")
        )
        all_tasks[get_or_create_policy_ref]["manifest_account_ids"].update(
            task_to_add.get("manifest_account_ids")
        )


def handle_stacks(
    all_tasks,
    all_tasks_task_reference,
    item_name,
    puppet_account_id,
    section_name,
    task_reference,
    task_to_add,
):
    prepare_task_reference = (
        f"{constants.PREPARE_ACCOUNT_FOR_STACKS}-{task_to_add.get('account_id')}"
    )
    if not all_tasks.get(prepare_task_reference):
        all_tasks[prepare_task_reference] = dict(
            task_reference=prepare_task_reference,
            account_id=task_to_add.get("account_id"),
            region=constants.HOME_REGION,
            puppet_account_id=puppet_account_id,
            dependencies_by_reference=[constants.CREATE_POLICIES],
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
            section_name=constants.PREPARE_ACCOUNT_FOR_STACKS,
        )
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        prepare_task_reference
    )
    all_tasks[prepare_task_reference]["manifest_section_names"].update(
        task_to_add.get("manifest_section_names")
    )
    all_tasks[prepare_task_reference]["manifest_item_names"].update(
        task_to_add.get("manifest_item_names")
    )
    all_tasks[prepare_task_reference]["manifest_account_ids"].update(
        task_to_add.get("manifest_account_ids")
    )

    get_s3_template_ref = f"{constants.GET_TEMPLATE_FROM_S3}-{section_name}-{item_name}"
    if not all_tasks.get(get_s3_template_ref):
        all_tasks[get_s3_template_ref] = dict(
            task_reference=get_s3_template_ref,
            execution="hub",
            bucket=task_to_add.get("bucket"),
            key=task_to_add.get("key"),
            region=task_to_add.get("region"),
            version_id=task_to_add.get("version_id"),
            puppet_account_id=puppet_account_id,
            account_id=puppet_account_id,
            dependencies_by_reference=[constants.CREATE_POLICIES],
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
            section_name=constants.GET_TEMPLATE_FROM_S3,
        )
    all_tasks[all_tasks_task_reference]["get_s3_template_ref"] = get_s3_template_ref
    all_tasks[all_tasks_task_reference]["dependencies_by_reference"].append(
        get_s3_template_ref
    )
    all_tasks[get_s3_template_ref]["manifest_section_names"].update(
        task_to_add.get("manifest_section_names")
    )
    all_tasks[get_s3_template_ref]["manifest_item_names"].update(
        task_to_add.get("manifest_item_names")
    )
    all_tasks[get_s3_template_ref]["manifest_account_ids"].update(
        task_to_add.get("manifest_account_ids")
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
            dependencies_by_reference=[constants.CREATE_POLICIES],
            account_id=task_to_add.get("account_id"),
            section_name=constants.WORKSPACE_ACCOUNT_PREPARATION,
            manifest_section_names=dict(),
            manifest_item_names=dict(),
            manifest_account_ids=dict(),
        )
    all_tasks[workspace_account_preparation_ref]["manifest_section_names"].update(
        task_to_add.get("manifest_section_names")
    )
    all_tasks[workspace_account_preparation_ref]["manifest_item_names"].update(
        task_to_add.get("manifest_item_names")
    )
    all_tasks[workspace_account_preparation_ref]["manifest_account_ids"].update(
        task_to_add.get("manifest_account_ids")
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
            elif sharing_mode == constants.SHARING_MODE_AWS_ORGANIZATIONS:
                share_and_accept_ref = f"portfolio_share_and_accept-{task_to_add.get('ou')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
            else:
                raise Exception(f"Unknown sharing mode: {sharing_mode}")

            if not all_tasks.get(share_and_accept_ref):
                all_tasks[share_and_accept_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    account_id=task_to_add.get("account_id"),
                    region=task_to_add.get("region"),
                    task_reference=share_and_accept_ref,
                    dependencies_by_reference=[
                        hub_portfolio_ref,
                        constants.CREATE_POLICIES,
                    ],
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
        elif sharing_mode == constants.SHARING_MODE_AWS_ORGANIZATIONS:
            share_and_accept_ref = f"portfolio_share_and_accept-{task_to_add.get('ou')}-{task_to_add.get('region')}-{task_to_add.get('portfolio')}"
        else:
            raise Exception(f"Unknown sharing mode: {sharing_mode}")
        if not all_tasks.get(share_and_accept_ref):
            all_tasks[share_and_accept_ref] = dict(
                puppet_account_id=puppet_account_id,
                account_id=task_to_add.get("account_id"),
                region=task_to_add.get("region"),
                task_reference=share_and_accept_ref,
                dependencies_by_reference=[
                    hub_portfolio_ref,
                    constants.CREATE_POLICIES,
                ],
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


def generate_hub_task_reference(puppet_account_id, all_tasks, output_file_path):
    tasks_to_include = dict()
    generate_manifest_ref = "generate-manifest"
    for task_name, task in all_tasks.get("all_tasks").items():
        execution = task.get("execution", constants.EXECUTION_MODE_DEFAULT)
        if execution in [constants.EXECUTION_MODE_HUB, constants.EXECUTION_MODE_ASYNC]:
            should_include = True
        elif execution == constants.EXECUTION_MODE_SPOKE:
            # should_include = False
            # sharing should happen from the hub for launches in spoke mode
            should_include = (
                task.get("section_name") == constants.PORTFOLIO_SHARE_AND_ACCEPT_ACCOUNT
            )

        elif execution == constants.EXECUTION_MODE_HUB_AND_SPOKE_SPLIT:
            # cannot assume account_id role from spoke when it is the puppet account id
            should_include = (
                task.get("account_id", puppet_account_id) == puppet_account_id
            )
            # these should not override the previous decisions
            if not should_include:
                # sharing should happen from the hub for spoke-local-portfolios in hub and spoke split mode
                should_include = task.get("section_name") in [
                    constants.PORTFOLIO_SHARE_AND_ACCEPT_ACCOUNT,
                    constants.PORTFOLIO_SHARE_AND_ACCEPT_AWS_ORGANIZATIONS,
                ]
        else:
            raise Exception("Unhandled execution")

        if should_include:
            tasks_to_include[task_name] = task
        else:
            if not tasks_to_include.get(generate_manifest_ref):
                tasks_to_include[generate_manifest_ref] = dict(
                    puppet_account_id=puppet_account_id,
                    task_reference=generate_manifest_ref,
                    section_name=constants.GENERATE_MANIFEST,
                    dependencies_by_reference=[],
                )

            replacement_ref = (
                f"{constants.RUN_DEPLOY_IN_SPOKE}_{task.get('account_id')}"
            )
            if not tasks_to_include.get(replacement_ref):
                tasks_to_include[replacement_ref] = dict(
                    execution=constants.EXECUTION_MODE_HUB,
                    puppet_account_id=puppet_account_id,
                    account_id=task.get("account_id"),
                    section_name=constants.RUN_DEPLOY_IN_SPOKE,
                    task_reference=replacement_ref,
                    generate_manifest_ref=generate_manifest_ref,
                    dependencies_by_reference=[generate_manifest_ref,],
                )

    # make sure everything runs before we zip up the output directory
    if tasks_to_include.get(generate_manifest_ref):
        t = tasks_to_include[generate_manifest_ref]
        for task_name, task_to_include in tasks_to_include.items():
            if task_to_include.get("section_name") not in [
                constants.RUN_DEPLOY_IN_SPOKE,
                constants.GENERATE_MANIFEST,
            ]:
                t["dependencies_by_reference"].append(task_name)

    for task_name, task_to_include in tasks_to_include.items():
        for dep in task_to_include.get("dependencies_by_reference"):
            if not tasks_to_include.get(dep):
                raise Exception(
                    f"{task_name} depends on: {dep} which is not listed in this reference"
                )

    result = dict(all_tasks=tasks_to_include)
    ensure_no_cyclic_dependencies("hub task reference", tasks_to_include)
    # open(output_file_path, "w").write(serialisation_utils.dump(result))
    open(output_file_path, "w").write(serialisation_utils.dump_as_json(result))
    return result


def generate_task_reference(f):
    path = os.path.dirname(f.name)
    puppet_account_id = config.get_puppet_account_id()

    content = open(f.name, "r").read()
    manifest = manifest_utils.Manifest(serialisation_utils.load(content))
    complete = generate_complete_task_reference(  # hub and spokes
        puppet_account_id,
        manifest,
        f.name.replace("-expanded.yaml", "-task-reference-full.json"),
    )
    hub_tasks = generate_hub_task_reference(  # hub only
        puppet_account_id,
        complete,
        f.name.replace("-expanded.yaml", "-task-reference.json"),
    )
    task_output_path = f"{path}/tasks"
    if not os.path.exists(task_output_path):
        os.makedirs(task_output_path)

    for t_name, task in complete.get("all_tasks", {}).items():
        task_output_file_path = f"{task_output_path}/{graph.escape(t_name)}.json"
        task_output_content = serialisation_utils.dump_as_json(task)
        open(task_output_file_path, "w").write(task_output_content)

    for t_name, task in hub_tasks.get("all_tasks", {}).items():
        task_output_file_path = f"{task_output_path}/{graph.escape(t_name)}.json"
        task_output_content = serialisation_utils.dump_as_json(task)
        open(task_output_file_path, "w").write(task_output_content)


def deploy_from_task_reference(path):
    f = f"{path}/manifest-task-reference.json"
    tasks_to_run = list()
    tasks_to_run_filtered = dict()
    reference = serialisation_utils.load_as_json(open(f, "r").read())
    all_tasks = reference.get("all_tasks")

    num_workers = config.get_num_workers()
    puppet_account_id = config.get_puppet_account_id()
    single_account_id = config.get_single_account_id()

    for task_reference, task in all_tasks.items():
        for a in [
            "manifest_section_names",
            "manifest_item_names",
            "manifest_account_ids",
        ]:
            if task.get(a):
                del task[a]

        if single_account_id:
            task_section_name = task.get("section_name")
            task_account_id = task.get("account_id")
            if str(config.get_executor_account_id()) != str(
                puppet_account_id
            ):  # SPOKE EXECUTION
                if (
                    task_account_id == single_account_id
                    and task_section_name != constants.RUN_DEPLOY_IN_SPOKE
                ):
                    tasks_to_run_filtered[task_reference] = task

            else:  # HUB EXECUTION
                print(task.get("task_reference"))

                if task.get("task_reference") == constants.CREATE_POLICIES:
                    continue

                if task_account_id and str(task_account_id) not in [
                    str(single_account_id),
                    str(puppet_account_id),
                ]:
                    continue

                tasks_to_run_filtered[task_reference] = task
        else:
            tasks_to_run_filtered[task_reference] = task

    executor_account_id = config.get_executor_account_id()
    is_dry_run = is_list_launches = False
    execution_mode = "hub"
    on_complete_url = config.get_on_complete_url()
    running_exploded = False
    output_cache_starting_point = ""

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
        tasks_to_run_filtered,
        path,
        f,
    )
