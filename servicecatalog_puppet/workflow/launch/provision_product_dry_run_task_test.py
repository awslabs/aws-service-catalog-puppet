#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class ProvisionProductDryRunTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    manifest_file_path = "manifest_file_path"
    launch_name = "launch_name"
    portfolio = "portfolio"
    product = "product"
    version = "version"
    region = "region"
    account_id = "account_id"
    puppet_account_id = "puppet_account_id"
    ssm_param_inputs = []
    launch_parameters = {}
    manifest_parameters = {}
    account_parameters = {}
    retry_count = 1
    worker_timeout = 3
    ssm_param_outputs = []
    should_use_sns = False

    requested_priority = 1
    execution = "execution"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.launch import provision_product_dry_run_task

        self.module = provision_product_dry_run_task

        self.sut = self.module.ProvisionProductDryRunTask(
            manifest_file_path=self.manifest_file_path,
            launch_name=self.launch_name,
            portfolio=self.portfolio,
            product=self.product,
            version=self.version,
            region=self.region,
            account_id=self.account_id,
            puppet_account_id=self.puppet_account_id,
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

    def test_api_calls_used(self):
        # setup
        expected_result = [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",
            f"cloudformation.describe_provisioning_artifact_{self.account_id}_{self.region}",
            f"cloudformation.get_template_summary_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
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
