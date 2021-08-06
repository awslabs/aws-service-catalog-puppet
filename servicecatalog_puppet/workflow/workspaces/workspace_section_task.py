#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generic import generic_section_task
from servicecatalog_puppet.workflow.workspaces import (
    workspace_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.workspaces import workspace_for_account_task
from servicecatalog_puppet.workflow.workspaces import workspace_for_region_task
from servicecatalog_puppet.workflow.workspaces import workspace_task


class WorkspaceSectionTask(generic_section_task.GenericSectionTask):
    """
    Iterates through the workspace items in the workspace section of the manifest file and generates the dependencies
    tasks and correct ForX tasks.
    """

    section_name_singular = constants.WORKSPACE
    section_name = constants.WORKSPACES
    for_region_task_klass = workspace_for_region_task.WorkspaceForRegionTask
    for_account_task_klass = workspace_for_account_task.WorkspaceForAccountTask
    for_account_and_region_task_klass = (
        workspace_for_account_and_region_task.WorkspaceForAccountAndRegionTask
    )
    task_klass = workspace_task.WorkspaceTask
    item_name = "workspace_name"
    supports_spoke_mode = True
