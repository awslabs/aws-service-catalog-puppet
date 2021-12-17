#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.general import get_ssm_param_task


class ServiceControlPoliciesBaseTask(get_ssm_param_task.PuppetTaskWithParameters):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.SERVICE_CONTROL_POLICIES

    @property
    def item_name(self):
        return self.service_control_policy_name

    @property
    def item_identifier(self):
        return "service_control_policy_name"
