#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip, mock

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class TagPoliciesTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    tag_policies_name = "tag_policies_name"
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.tag_policies import tag_policies_task

        self.module = tag_policies_task

        self.sut = self.module.TagPoliciesTask(
            manifest_file_path=self.manifest_file_path,
            tag_policies_name=self.tag_policies_name,
            puppet_account_id=self.puppet_account_id,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "tag_policies_name": self.tag_policies_name,
            "cache_invalidator": self.cache_invalidator,
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

    @mock.patch(
        "servicecatalog_puppet.workflow.manifest.manifest_mixin.ManifestMixen.manifest"
    )
    def test_requires(self, manifest_mock):
        # setup
        requirements = list()

        klass = self.sut.get_klass_for_provisioning()
        for (
            account_id,
            regions,
        ) in self.sut.manifest.get_account_ids_and_regions_used_for_section_item(
            self.sut.puppet_account_id,
            self.sut.section_name,
            self.sut.tag_policies_name,
        ).items():
            for region in regions:
                for (
                    task
                ) in self.sut.manifest.get_tasks_for_launch_and_account_and_region(
                    self.sut.puppet_account_id,
                    self.sut.section_name,
                    self.sut.tag_policies_name,
                    account_id,
                    region,
                ):
                    requirements.append(
                        klass(**task, manifest_file_path=self.sut.manifest_file_path)
                    )

        expected_result = requirements

        # exercise
        actual_result = self.sut.requires()

        # assert
        self.assertEqual(expected_result, actual_result)
