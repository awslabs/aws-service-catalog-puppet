#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generic import generic_section_task
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_for_account_task,
)
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_for_region_task,
)
from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_task


class LambdaInvocationsSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.LAMBDA_INVOCATION
    section_name = constants.LAMBDA_INVOCATIONS
    for_region_task_klass = (
        lambda_invocation_for_region_task.LambdaInvocationForRegionTask
    )
    for_account_task_klass = (
        lambda_invocation_for_account_task.LambdaInvocationForAccountTask
    )
    for_account_and_region_task_klass = (
        lambda_invocation_for_account_and_region_task.LambdaInvocationForAccountAndRegionTask
    )
    task_klass = lambda_invocation_task.LambdaInvocationTask
    item_name = "lambda_invocation_name"
    supports_spoke_mode = True
