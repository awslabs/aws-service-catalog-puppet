#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import copy

from deepmerge import always_merger

from servicecatalog_puppet import (
    config,
    constants,
    serialisation_utils,
    task_reference_constants,
)
from servicecatalog_puppet.commands import graph
from servicecatalog_puppet.commands.task_reference_helpers.generators import generator
from servicecatalog_puppet.commands.task_reference_helpers.generators.boto3_parameter_handler import (
    boto3_parameter_handler,
)
from servicecatalog_puppet.commands.task_reference_helpers.generators.ssm_outputs_handler import (
    ssm_outputs_handler,
)
from servicecatalog_puppet.commands.task_reference_helpers.generators.ssm_parameter_handler import (
    ssm_parameter_handler,
)
from servicecatalog_puppet.waluigi.shared_tasks.task_topological_generations_without_scheduler_unit_test import (
    dependency_task_reference,
)
from servicecatalog_puppet.workflow import workflow_utils
from servicecatalog_puppet.workflow.dependencies import resources_factory


def generate(puppet_account_id, manifest, output_file_directory_path):
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

    all_tasks[constants.CREATE_POLICIES] = {
        "execution": constants.EXECUTION_MODE_HUB,
        task_reference_constants.MANIFEST_SECTION_NAMES: dict(),
        task_reference_constants.MANIFEST_ITEM_NAMES: dict(),
        "account_id": puppet_account_id,
        "region": default_region,
        task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
        "task_reference": constants.CREATE_POLICIES,
        "dependencies_by_reference": list(),
        "section_name": constants.CREATE_POLICIES,
        "organizations_to_share_with": list(organizations_to_share_with.keys()),
        "ous_to_share_with": list(ous_to_share_with.keys()),
        "accounts_to_share_with": list(accounts_to_share_with.keys()),
    }

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
                task_to_add[task_reference_constants.MANIFEST_SECTION_NAMES] = {
                    section_name: True
                }
                task_to_add[task_reference_constants.MANIFEST_ITEM_NAMES] = {
                    item_name: True
                }
                task_to_add[task_reference_constants.MANIFEST_ACCOUNT_IDS] = {
                    task_to_add.get("account_id"): True
                }
                task_to_add["section_name"] = section_name
                task_to_add["item_name"] = item_name
                # set up for later pass
                task_to_add["dependencies_by_reference"] = [constants.CREATE_POLICIES]
                task_reference = graph.escape(
                    f"{task_to_add.get('ou_name', task_to_add.get('account_id'))}-{task_to_add.get('region')}"
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

                ssm_outputs_handler(
                    all_tasks,
                    all_tasks_task_reference,
                    default_region,
                    item_name,
                    puppet_account_id,
                    section_name,
                    task_to_add,
                )

                generator.generate(
                    all_tasks,
                    all_tasks_task_reference,
                    item_name,
                    puppet_account_id,
                    section_name,
                    task_reference,
                    task_to_add,
                    manifest,
                )

                task = task_to_add  # TODO rename
                new_tasks = all_tasks  # TODO rename
                parameters = {}
                launch_parameters = (
                    manifest.get(task.get("section_name"), {})
                    .get(task.get("item_name"), {})
                    .get("parameters", {})
                )
                manifest_parameters = copy.deepcopy(manifest.get("parameters"))
                account_parameters = manifest.get_parameters_for_account(
                    task.get("account_id")
                )

                always_merger.merge(parameters, manifest_parameters)
                always_merger.merge(parameters, launch_parameters)
                always_merger.merge(parameters, account_parameters)

                if task.get("status") != constants.TERMINATED:
                    for parameter_name, parameter_details in parameters.items():
                        ssm_parameter_handler(
                            all_tasks,
                            default_region,
                            new_tasks,
                            parameter_details,
                            puppet_account_id,
                            task,
                        )
                        boto3_parameter_handler(
                            new_tasks,
                            parameter_details,
                            parameter_name,
                            puppet_account_id,
                            task,
                        )

    #
    # Second pass - replacing dependencies with dependencies_by_reference and adding resources
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

    #
    # Third pass - setting dependencies between parameters and outputs
    #
    for task_reference, task in all_tasks.items():
        # wire up dependencies for SSM parameters to outputs
        ssm_parameters = task.get("ssm_parameters_tasks_references", {}).items()
        dependencies_to_add = []
        for parameter_name, parameter_task_reference in ssm_parameters:
            for dependency in task.get("dependencies_by_reference"):
                ssm_outputs = (
                    all_tasks.get(dependency)
                    .get("ssm_outputs_tasks_references", {})
                    .items()
                )
                for output_name, output_task_reference in ssm_outputs:
                    if (
                        output_task_reference.replace(
                            constants.SSM_OUTPUTS, constants.SSM_PARAMETERS
                        )
                        == parameter_task_reference
                    ):
                        dependencies_to_add.append(output_task_reference)
                        all_tasks[parameter_task_reference][
                            "dependencies_by_reference"
                        ].append(output_task_reference)
        task["dependencies_by_reference"].extend(dependencies_to_add)

        # wire up dependencies for boto3 parameters
        boto3_parameters = task.get("boto3_parameters_tasks_references", {}).items()
        dependencies_to_add = []
        for parameter_name, parameter_task_reference in boto3_parameters:
            parameter_task = all_tasks.get(parameter_task_reference)
            for dependency_task_reference in task.get("dependencies_by_reference"):
                if dependency_task_reference not in parameter_task.get(
                    "dependencies_by_reference"
                ):
                    if dependency_task_reference != parameter_task_reference:
                        if (
                            all_tasks[dependency_task_reference]["section_name"]
                            in constants.ALL_SECTION_NAMES
                        ):
                            parameter_task["dependencies_by_reference"].append(
                                dependency_task_reference
                            )

            if task_reference in parameter_task["dependencies_by_reference"]:
                parameter_task["dependencies_by_reference"].remove(task_reference)

    #
    # Fourth pass - removing cyclic dependencies caused by a->b->c when using boto3 parameters
    #
    for task_reference, task in all_tasks.items():
        # remove dependencies on self
        boto3_parameters = task.get("boto3_parameters_tasks_references", {}).items()
        dependencies_to_add = []
        for parameter_name, parameter_task_reference in boto3_parameters:
            parameter_task = all_tasks.get(parameter_task_reference)
            if task_reference in parameter_task.get("dependencies_by_reference"):
                parameter_task["dependencies_by_reference"].remove(task_reference)

    for _, tasks_by_section in tasks_by_account_id.items():
        for section_name, section_tasks in tasks_by_section.items():
            for account_id, account_tasks in section_tasks.items():
                all_tasks_for_account = dict()
                for task_for_account_reference in account_tasks:
                    all_tasks_for_account[task_for_account_reference] = all_tasks.get(
                        task_for_account_reference
                    )
                output_file_path = f"{output_file_directory_path}/manifest-task-reference-{account_id}.json"
                open(output_file_path, "w").write(
                    serialisation_utils.dump_as_json(
                        dict(all_tasks=all_tasks_for_account)
                    )
                )

    reference = dict(all_tasks=all_tasks,)
    workflow_utils.ensure_no_cyclic_dependencies("complete task reference", all_tasks)
    output_file_path = output_file_directory_path + "/manifest-task-reference-full.json"
    open(output_file_path, "w").write(serialisation_utils.dump_as_json(reference))
    return reference
