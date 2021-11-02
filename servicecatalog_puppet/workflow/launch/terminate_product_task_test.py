#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class TerminateProductTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    portfolio = "portfolio"
    portfolio_id = "portfolio_id"
    product = "product"
    product_id = "product_id"
    version = "version"
    version_id = "version_id"
    account_id = "account_id"
    region = "region"
    puppet_account_id = "puppet_account_id"
    retry_count = 1
    ssm_param_outputs = []
    worker_timeout = 3
    parameters = {}
    ssm_param_inputs = []
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import terminate_product_task

        self.module = terminate_product_task

        self.sut = self.module.TerminateProductTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            account_id=self.account_id,
            region=self.region,
            puppet_account_id=self.puppet_account_id,
            retry_count=self.retry_count,
            ssm_param_outputs=self.ssm_param_outputs,
            worker_timeout=self.worker_timeout,
            ssm_param_inputs=self.ssm_param_inputs,
            execution=self.execution,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_api_calls_used(self):
        # setup
        expected_result = []

        # exercise
        actual_result = self.sut.api_calls_used()

        # verify
        self.assertEqual(expected_result, actual_result)

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
