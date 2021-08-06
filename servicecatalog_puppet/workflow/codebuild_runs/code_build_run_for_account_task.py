#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_for_task
from servicecatalog_puppet.workflow.generic import generic_for_account_task


class CodeBuildRunForAccountTask(
    generic_for_account_task.GenericForAccountTask,
    code_build_run_for_task.CodeBuildRunForTask,
):
    account_id = luigi.Parameter()
