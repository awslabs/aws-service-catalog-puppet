#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generic import generic_section_task
from servicecatalog_puppet.workflow.stack import stack_for_account_and_region_task
from servicecatalog_puppet.workflow.stack import stack_for_account_task
from servicecatalog_puppet.workflow.stack import stack_for_region_task
from servicecatalog_puppet.workflow.stack import stack_task


class StackSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.STACK
    section_name = constants.STACKS
    for_region_task_klass = stack_for_region_task.StackForRegionTask
    for_account_task_klass = stack_for_account_task.StackForAccountTask
    for_account_and_region_task_klass = (
        stack_for_account_and_region_task.StackForAccountAndRegionTask
    )
    task_klass = stack_task.StackTask
    item_name = "stack_name"
    supports_spoke_mode = True
