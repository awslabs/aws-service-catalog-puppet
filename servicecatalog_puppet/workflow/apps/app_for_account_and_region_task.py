#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.apps import app_for_task
from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task


class AppForAccountAndRegionTask(
    generic_for_account_and_region_task.GenericForAccountAndRegionTask,
    app_for_task.AppForTask,
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
