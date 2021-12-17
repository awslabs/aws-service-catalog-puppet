#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow.service_control_policies import (
    service_control_policies_for_task,
)
from servicecatalog_puppet.workflow.generic import generic_for_account_task


class ServiceControlPoliciesForAccountTask(
    generic_for_account_task.GenericForAccountTask,
    service_control_policies_for_task.ServiceControlPoliciesForTask,
):
    account_id = luigi.Parameter()
