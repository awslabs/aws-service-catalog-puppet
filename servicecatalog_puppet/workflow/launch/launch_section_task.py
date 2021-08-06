#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generic import generic_section_task
from servicecatalog_puppet.workflow.launch import launch_for_account_and_region_task
from servicecatalog_puppet.workflow.launch import launch_for_account_task
from servicecatalog_puppet.workflow.launch import launch_for_region_task
from servicecatalog_puppet.workflow.launch import launch_task


class LaunchSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.LAUNCH
    section_name = constants.LAUNCHES
    for_region_task_klass = launch_for_region_task.LaunchForRegionTask
    for_account_task_klass = launch_for_account_task.LaunchForAccountTask
    for_account_and_region_task_klass = (
        launch_for_account_and_region_task.LaunchForAccountAndRegionTask
    )
    task_klass = launch_task.LaunchTask
    item_name = "launch_name"
    supports_spoke_mode = True
