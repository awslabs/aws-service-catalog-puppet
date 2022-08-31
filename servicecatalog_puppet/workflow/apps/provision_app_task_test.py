#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import TestCase


class TestProvisionAppTask(TestCase):
    cache_invalidator = 'NOW'
    account_id = 'account_id'
    region = "region"
    app_name = 'app'
    puppet_account_id = 'pupp'
    task_reference = 'task_reference'
    manifest_task_reference_file_path = "manifest_task_reference_file_path"
    dependencies_by_reference = []

    bucket = 'bucket'
    key = 'key'
    version_id = 'version_id'
    execution = 'execution'

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.apps import provision_app_task
        self.sut = provision_app_task.ProvisionAppTask(
            task_reference=self.task_reference,
            puppet_account_id=self.puppet_account_id,
            app_name=self.app_name,
            region=self.region,
            account_id=self.account_id,
            manifest_task_reference_file_path=self.manifest_task_reference_file_path,
            dependencies_by_reference=self.dependencies_by_reference,
            bucket=self.bucket,
            key=self.key,
            version_id=self.version_id,
            execution=self.execution,
        )

    def test_params_for_results_display(self):
        # setup
        expected_results = {
            "task_reference": self.task_reference,
            "puppet_account_id": self.puppet_account_id,
            "app_name": self.app_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_results = self.sut.params_for_results_display()

        self.assertEqual(expected_results, actual_results)
