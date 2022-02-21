#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.tag_policies import tag_policies_task

from servicecatalog_puppet.workflow.generic import generic_section_task


class TagPoliciesSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.TAG_POLICY
    section_name = constants.TAG_POLICIES
    for_region_task_klass = None
    for_account_task_klass = None
    for_account_and_region_task_klass = None
    task_klass = tag_policies_task.TagPoliciesTask
    item_name = "tag_policies_name"
    supports_spoke_mode = False
