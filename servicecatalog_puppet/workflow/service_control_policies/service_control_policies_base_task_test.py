#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ServiceControlPoliciesBaseTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.service_control_policies import (
            service_control_policies_base_task,
        )

        self.module = service_control_policies_base_task

        self.sut = self.module.ServiceControlPoliciesBaseTask(
            manifest_file_path=self.manifest_file_path
        )

        self.wire_up_mocks()
