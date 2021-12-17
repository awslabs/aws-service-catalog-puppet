#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.service_control_policies import (
    service_control_policies_for_task,
)
from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task


class ServiceControlPoliciesForAccountAndRegionTask(
    generic_for_account_and_region_task.GenericForAccountAndRegionTask,
    service_control_policies_for_task.ServiceControlPoliciesForTask,
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
