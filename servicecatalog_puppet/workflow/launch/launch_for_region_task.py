#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.generic import generic_for_region_task
from servicecatalog_puppet.workflow.launch import launch_for_task


class LaunchForRegionTask(
    generic_for_region_task.GenericForRegionTask, launch_for_task.LaunchForTask
):
    region = luigi.Parameter()
