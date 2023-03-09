#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ProvisioningArtifactParametersTaskTest(
    tasks_unit_tests_helper.PuppetTaskUnitTest
):
    portfolio = "portfolio"
    product = "product"
    version = "version"
    region = "region"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import (
            provisioning_artifact_parameters_task,
        )

        self.module = provisioning_artifact_parameters_task

        self.sut = self.module.ProvisioningArtifactParametersTask(
            **self.get_common_args(),
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            region=self.region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "region": self.region,
            "product": self.product,
            "version": self.version,
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
