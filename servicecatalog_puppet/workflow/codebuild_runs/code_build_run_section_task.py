#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.codebuild_runs import (
    code_build_run_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.codebuild_runs import (
    code_build_run_for_account_task,
)
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_for_region_task
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_task

from servicecatalog_puppet.workflow.generic import generic_section_task


class CodeBuildRunsSectionTask(generic_section_task.GenericSectionTask):
    section_name_singular = constants.CODE_BUILD_RUN
    section_name = constants.CODE_BUILD_RUNS
    for_region_task_klass = code_build_run_for_region_task.CodeBuildRunForRegionTask
    for_account_task_klass = code_build_run_for_account_task.CodeBuildRunForAccountTask
    for_account_and_region_task_klass = (
        code_build_run_for_account_and_region_task.CodeBuildRunForAccountAndRegionTask
    )
    task_klass = code_build_run_task.CodeBuildRunTask
    item_name = "code_build_run_name"
    supports_spoke_mode = True
