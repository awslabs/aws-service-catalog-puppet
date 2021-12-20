#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.service_control_policies import (
    service_control_policies_task,
)

from servicecatalog_puppet.workflow.generic import generic_section_task


class ServiceControlPoliciesSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.SERVICE_CONTROL_POLICY
    section_name = constants.SERVICE_CONTROL_POLICIES
    for_region_task_klass = None
    for_account_task_klass = None
    for_account_and_region_task_klass = None
    task_klass = service_control_policies_task.ServiceControlPoliciesTask
    item_name = "service_control_policies_name"
    supports_spoke_mode = False
