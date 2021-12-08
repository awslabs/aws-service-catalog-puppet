#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class BootstrapSpokeAsTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    puppet_account_id = "puppet_account_id"
    account_id = "account_id"
    iam_role_arns = []
    role_name = "role_name"
    permission_boundary = "permission_boundary"
    puppet_role_name = "puppet_role_name"
    puppet_role_path = "puppet_role_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow import management

        self.module = management

        self.sut = self.module.BootstrapSpokeAsTask(
            puppet_account_id=self.puppet_account_id,
            account_id=self.account_id,
            iam_role_arns=self.iam_role_arns,
            role_name=self.role_name,
            permission_boundary=self.permission_boundary,
            puppet_role_name=self.puppet_role_name,
            puppet_role_path=self.puppet_role_path,
            tag=[],
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
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
