#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
import os


from servicecatalog_puppet import manifest_utils, constants, serialisation_utils, config
from servicecatalog_puppet.commands import graph
from servicecatalog_puppet.commands.task_reference_helpers import (
    hub_generator,
    complete_generator,
)
from servicecatalog_puppet.workflow import runner, workflow_utils

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def generate_task_reference(f):
    path = os.path.dirname(f.name)
    puppet_account_id = config.get_puppet_account_id()

    content = open(f.name, "r").read()
    manifest = manifest_utils.Manifest(serialisation_utils.load(content))
    complete = complete_generator.generate(  # hub and spokes
        puppet_account_id,
        manifest,
        f.name.replace("-expanded.yaml", "-task-reference-full.json"),
    )
    hub_tasks = hub_generator.generate(  # hub only
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
        if single_account_id:
            task_section_name = task.get("section_name")
            task_account_id = task.get("account_id")
            spoke_execution = str(config.get_executor_account_id()) != str(
                puppet_account_id
            )
            if spoke_execution:
                if (
                    task_account_id == single_account_id
                    and task_section_name != constants.RUN_DEPLOY_IN_SPOKE
                ):
                    tasks_to_run_filtered[task_reference] = task

            else:
                if task.get("task_reference") == constants.CREATE_POLICIES:
                    continue

                if task.get("section_name") == constants.SSM_OUTPUTS:
                    if not any(
                        [
                            task.get("manifest_account_ids").get(
                                str(single_account_id)
                            ),
                            task.get("manifest_account_ids").get(
                                str(puppet_account_id)
                            ),
                        ]
                    ):
                        continue

                else:
                    if task_account_id and str(task_account_id) not in [
                        str(single_account_id),
                        str(puppet_account_id),
                    ]:
                        continue

                tasks_to_run_filtered[task_reference] = task
        else:
            tasks_to_run_filtered[task_reference] = task

        for a in [
            "manifest_section_names",
            "manifest_item_names",
            "manifest_account_ids",
        ]:
            if task.get(a):
                del task[a]

    executor_account_id = config.get_executor_account_id()
    is_dry_run = is_list_launches = False
    execution_mode = config.get_execution_mode()
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
