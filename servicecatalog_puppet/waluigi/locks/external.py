#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import serialisation_utils
from servicecatalog_puppet.waluigi.constants import RESOURCES_REQUIRED
from servicecatalog_puppet.waluigi.dag_utils import logger


def are_resources_are_free_for_task(task_parameters: dict, resources_file_path: str):
    with open(resources_file_path, "rb") as f:
        resources_in_use = serialisation_utils.json_loads(f.read())
    return are_resources_are_free_for_task_dict(task_parameters, resources_in_use)


def are_resources_are_free_for_task_dict(task_parameters, resources_in_use):
    return (
        all(
            resources_in_use.get(r, False) is False
            for r in task_parameters.get(RESOURCES_REQUIRED, [])
        ),
        resources_in_use,
    )


def lock_resources_for_task(
    task_reference: str,
    task_parameters: dict,
    resources_in_use: dict,
    resources_file_path: str,
):
    # print(f"Worker locking {task_reference}")
    for r in task_parameters.get(RESOURCES_REQUIRED, []):
        resources_in_use[r] = task_reference
    with open(resources_file_path, "wb") as f:
        f.write(serialisation_utils.json_dumps(resources_in_use))


def unlock_resources_for_task(task_parameters: dict, resources_file_path: str):
    with open(resources_file_path, "rb") as f:
        resources_in_use = serialisation_utils.json_loads(f.read())
    for r in task_parameters.get(RESOURCES_REQUIRED, []):
        try:
            del resources_in_use[r]
        except KeyError:
            logger.warn(
                f"{task_parameters.get('task_reference')} tried to unlock {r} but it wasn't present"
            )
    with open(resources_file_path, "wb") as f:
        f.write(serialisation_utils.json_dumps(resources_in_use))
