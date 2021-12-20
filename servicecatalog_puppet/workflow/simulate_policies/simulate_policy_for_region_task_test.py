#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import mock

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class SimulatePolicyForRegionTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    region = "region"
    puppet_account_id = "puppet_account_id"
    simulate_policy_name = "simulate_policy_name"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.simulate_policies import (
            simulate_policy_for_region_task,
        )

        self.module = simulate_policy_for_region_task

        self.sut = self.module.SimulatePolicyForRegionTask(
            manifest_file_path=self.manifest_file_path,
            simulate_policy_name=self.simulate_policy_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "simulate_policy_name": self.simulate_policy_name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    @mock.patch(
        "servicecatalog_puppet.workflow.manifest.manifest_mixin.ManifestMixen.manifest"
    )
    def test_requires(self, manifest_mock):
        # setup
        dependencies = list()
        these_dependencies = list()
        requirements = dict(
            dependencies=dependencies, these_dependencies=these_dependencies,
        )

        klass = self.sut.get_klass_for_provisioning()

        for task in self.sut.manifest.get_tasks_for_launch_and_region(
            self.sut.puppet_account_id,
            self.sut.section_name,
            self.sut.simulate_policy_name,
            self.sut.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.sut.manifest_file_path)
            )

        expected_result = requirements

        # exercise
        actual_result = self.sut.requires()

        # assert
        self.assertEqual(expected_result, actual_result)
