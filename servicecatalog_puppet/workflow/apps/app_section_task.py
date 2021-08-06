#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.apps import app_for_account_and_region_task
from servicecatalog_puppet.workflow.apps import app_for_account_task
from servicecatalog_puppet.workflow.apps import app_for_region_task
from servicecatalog_puppet.workflow.apps import app_task
from servicecatalog_puppet.workflow.generic import generic_section_task


class AppSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.APP
    section_name = constants.APPS
    for_region_task_klass = app_for_region_task.AppForRegionTask
    for_account_task_klass = app_for_account_task.AppForAccountTask
    for_account_and_region_task_klass = (
        app_for_account_and_region_task.AppForAccountAndRegionTask
    )
    task_klass = app_task.AppTask
    item_name = "app_name"
    supports_spoke_mode = True
