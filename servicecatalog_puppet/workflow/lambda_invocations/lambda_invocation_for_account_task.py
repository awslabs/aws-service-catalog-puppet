#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.generic import generic_for_account_task
from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_for_task


class LambdaInvocationForAccountTask(
    generic_for_account_task.GenericForAccountTask,
    lambda_invocation_for_task.LambdaInvocationForTask,
):
    account_id = luigi.Parameter()
