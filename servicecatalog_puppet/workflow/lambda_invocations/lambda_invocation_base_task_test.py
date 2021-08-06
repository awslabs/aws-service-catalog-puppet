#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class LambdaInvocationBaseTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            lambda_invocation_base_task,
        )

        self.module = lambda_invocation_base_task

        self.sut = self.module.LambdaInvocationBaseTask(
            manifest_file_path=self.manifest_file_path
        )

        self.wire_up_mocks()
