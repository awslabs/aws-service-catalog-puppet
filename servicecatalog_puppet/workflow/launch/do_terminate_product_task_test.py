#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class DoTerminateProductTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    puppet_account_id = "puppet_account_id"
    region = "region"
    account_id = "account_id"
    portfolio = "portfolio"
    product = "product"
    version = "version"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    retry_count = 1
    worker_timeout = 3
    ssm_param_outputs = []
    requested_priority = 1
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import do_terminate_product_task

        self.module = do_terminate_product_task

        self.sut = self.module.DoTerminateProductTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            puppet_account_id=self.puppet_account_id,
            region=self.region,
            account_id=self.account_id,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            ssm_param_inputs=self.ssm_param_inputs,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            retry_count=self.retry_count,
            worker_timeout=self.worker_timeout,
            ssm_param_outputs=self.ssm_param_outputs,
            requested_priority=self.requested_priority,
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
        expected_result = [
            f"servicecatalog.scan_provisioned_products_single_page{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",
            # f"ssm.delete_parameter_{self.region}": 1,
        ]

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
