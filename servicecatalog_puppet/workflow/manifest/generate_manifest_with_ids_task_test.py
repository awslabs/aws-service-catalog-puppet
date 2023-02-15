#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GenerateManifestWithIdsTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    task_reference = "task_reference"
    manifest_task_reference_file_path = "manifest_task_reference_file_path"
    dependencies_by_reference = "dependencies_by_reference"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.manifest import (
            generate_manifest_with_ids_task,
        )

        self.module = generate_manifest_with_ids_task

        self.sut = self.module.GenerateManifestWithIdsTask(**self.get_common_args())

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
