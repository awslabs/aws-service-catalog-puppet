#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import os
from datetime import datetime

from servicecatalog_puppet import manifest_utils, constants, yaml_utils, config
from servicecatalog_puppet.workflow import runner
from servicecatalog_puppet.workflow.stack.provision_stack_task import ProvisionStackTask


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
    # First pass - handle tasks and create ssm output tasks
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
            task_id_prefix = f"{section_name}_{item_name}"
            tasks_to_add = manifest.get_tasks_for(
                puppet_account_id, section_name, item_name
            )
            for task_to_add in tasks_to_add:
                task_to_add["section_name"] = section_name
                task_to_add["item_name"] = item_name
                del task_to_add["manifest_parameters"]  # TODO remove
                task_id = f"{task_to_add.get('account_id')}-{task_to_add.get('region')}"
                all_tasks_task_id = f"{task_id_prefix}_{task_id}"
                task_to_add["task_id"] = all_tasks_task_id
                all_tasks[all_tasks_task_id] = task_to_add
                tasks_by_type[section_name_singular][item_name].append(
                    all_tasks_task_id
                )

                if not tasks_by_region[section_name_singular][item_name].get(
                    task_to_add.get("region")
                ):
                    tasks_by_region[section_name_singular][item_name][
                        task_to_add.get("region")
                    ] = list()
                tasks_by_region[section_name_singular][item_name][
                    task_to_add.get("region")
                ].append(all_tasks_task_id)

                if not tasks_by_account_id[section_name_singular][item_name].get(
                    task_to_add.get("account_id")
                ):
                    tasks_by_account_id[section_name_singular][item_name][
                        task_to_add.get("account_id")
                    ] = list()
                tasks_by_account_id[section_name_singular][item_name][
                    task_to_add.get("account_id")
                ].append(all_tasks_task_id)

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
                ].append(all_tasks_task_id)

                # ssm outputs
                for ssm_parameter_output in task_to_add.get("ssm_param_outputs", []):
                    output_region = ssm_parameter_output.get("region", default_region)
                    ssm_parameter_output_task_id = f'ssm_outputs-{task_to_add.get("account_id")}-{output_region}-{ssm_parameter_output.get("param_name")}'
                    ssm_parameter_output_task_id = ssm_parameter_output_task_id.replace(
                        "${AWS::Region}", task_to_add.get("region")
                    ).replace("${AWS::AccountId}", task_to_add.get("account_id"))
                    if all_tasks.get(ssm_parameter_output_task_id):
                        raise Exception(
                            f"You have two tasks outputting the same SSM parameter output: {ssm_parameter_output.get('param_name')}"
                        )
                    all_tasks[ssm_parameter_output_task_id] = dict(
                        **ssm_parameter_output,
                        account_id=task_to_add.get("account_id"),
                        region=output_region,
                        dependencies_by_reference=[all_tasks_task_id],
                        section_name="ssm_outputs",
                    )

    #
    # Second pass - adding get parameters
    #
    # TODO handle account and manifest parameters
    # TODO handle boto3 parameters
    new_tasks = dict()
    for task_id, task in all_tasks.items():
        parameters = task.get("launch_parameters", {})
        for parameter_name, parameter_details in parameters.items():
            if parameter_details.get("ssm"):
                ssm_parameter_details = parameter_details.get("ssm")
                interpolation_output_account = task.get("account_id")
                interpolation_output_region = task.get("region")
                owning_account = ssm_parameter_details.get(
                    "account_id", puppet_account_id
                )
                owning_region = ssm_parameter_details.get("region", default_region)
                task_id = f"{owning_account}-{owning_region}"
                param_name = (
                    ssm_parameter_details.get("name")
                    .replace("${AWS::Region}", interpolation_output_region)
                    .replace("${AWS::AccountId}", interpolation_output_account)
                )
                ssm_parameter_task_id = f"ssm_parameters-{task_id}-{param_name}"
                if all_tasks.get(
                    ssm_parameter_task_id.replace("ssm_parameters-", "ssm_outputs-")
                ):
                    dependency = [
                        ssm_parameter_task_id.replace("ssm_parameters-", "ssm_outputs-")
                    ]
                else:
                    dependency = []
                new_tasks[ssm_parameter_task_id] = dict(
                    account_id=owning_account,
                    region=owning_region,
                    param_name=param_name,
                    dependencies_by_reference=dependency,
                    section_name="ssm_parameters",
                )
                if not task.get("dependencies_by_reference"):
                    task["dependencies_by_reference"] = list()
                task["dependencies_by_reference"].append(ssm_parameter_task_id)
    all_tasks.update(new_tasks)

    #
    # Third pass - replacing dependencies with dependencies_by_reference
    #
    for task_id, task in all_tasks.items():
        if not task.get("dependencies_by_reference"):
            task["dependencies_by_reference"] = list()

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

    reference = dict(
        all_tasks=all_tasks,
        # tasks_by_type=tasks_by_type,
    )
    open(f.name.replace("-expanded", "-task-reference"), "w").write(
        yaml_utils.dump(reference)
    )


def deploy_from_task_reference(f):
    puppet_account_id = config.get_puppet_account_id()

    tasks_to_run = list()
    reference = yaml_utils.load(open(f.name, "r").read())
    for task_id, task in reference.get("all_tasks").items():
        section_name = task.get("section_name")
        if section_name == constants.SSM_OUTPUTS:
            pass
        elif section_name == constants.SSM_PARAMETERS:
            pass
        elif section_name == constants.STACKS:
            tasks_to_run.append(
                ProvisionStackTask(
                    task_reference = task_id,
                    manifest_task_reference_file_path=f.name,
                    dependencies_by_reference=task.get("dependencies_by_reference"),
                    stack_name=task.get("stack_name"),
                    puppet_account_id=puppet_account_id,
                    region=task.get("region"),
                    account_id=task.get("account_id"),
                    bucket=task.get("bucket"),
                    key=task.get("key"),
                    version_id=task.get("version_id"),
                    launch_name=task.get("launch_name"),
                    stack_set_name=task.get("stack_set_name"),
                    capabilities=task.get("capabilities"),
                    ssm_param_inputs=[],
                    launch_parameters=task.get(""),
                    manifest_parameters=task.get(""),
                    account_parameters=task.get(""),
                    retry_count=task.get("retry_count"),
                    worker_timeout=task.get("worker_timeout"),
                    ssm_param_outputs=[],
                    requested_priority=task.get("requested_priority"),
                    use_service_role=task.get("use_service_role"),
                    execution=task.get("execution"),
                    manifest_file_path="ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml",
                )
            )
        else:
            raise Exception(f"Unhandled section_name: {section_name}")

    puppet_account_id = config.get_puppet_account_id()
    executor_account_id = puppet_account_id
    num_workers = 10
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
