#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ProvisioningTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import provisioning_task

        self.module = provisioning_task

        self.sut = self.module.ProvisioningTask(
            manifest_file_path=self.manifest_file_path
        )

        self.wire_up_mocks()
