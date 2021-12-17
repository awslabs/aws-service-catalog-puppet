#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.service_control_policies import (
    service_control_policies_for_task,
)
from servicecatalog_puppet.workflow.generic import generic_for_region_task


class ServiceControlPoliciesForRegionTask(
    generic_for_region_task.GenericForRegionTask,
    service_control_policies_for_task.ServiceControlPoliciesForTask,
):
    region = luigi.Parameter()
