#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import copy

from deepmerge import always_merger

from servicecatalog_puppet import config, constants, serialisation_utils
from servicecatalog_puppet.commands.task_reference_helpers.generators import generator
from servicecatalog_puppet.workflow import workflow_utils
from servicecatalog_puppet.workflow.dependencies import resources_factory


def generate(puppet_account_id, manifest, output_file_path):
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

                generator.generate(
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
    workflow_utils.ensure_no_cyclic_dependencies("complete task reference", all_tasks)
    open(output_file_path, "w").write(serialisation_utils.dump_as_json(reference))
    return reference
