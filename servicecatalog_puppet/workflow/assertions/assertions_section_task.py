#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.assertions import (
    assertion_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.assertions import assertion_for_account_task
from servicecatalog_puppet.workflow.assertions import assertion_for_region_task
from servicecatalog_puppet.workflow.assertions import assertion_task

from servicecatalog_puppet.workflow.generic import generic_section_task


class AssertionsSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.ASSERTION
    section_name = constants.ASSERTIONS
    for_region_task_klass = assertion_for_region_task.AssertionForRegionTask
    for_account_task_klass = assertion_for_account_task.AssertionForAccountTask
    for_account_and_region_task_klass = (
        assertion_for_account_and_region_task.AssertionForAccountAndRegionTask
    )
    task_klass = assertion_task.AssertionTask
    item_name = "assertion_name"
    supports_spoke_mode = True
