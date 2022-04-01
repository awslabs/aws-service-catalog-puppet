#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest import skip

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GetSSMParamTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    parameter_name = "parameter_name"
    name = "name"
    region = "region"
    default_value = "default_value"
    depends_on = []
    manifest_file_path = "manifest_file_path"
    puppet_account_id = "puppet_account_id"
    spoke_account_id = "spoke_account_id"
    spoke_region = "spoke_region"
    path = "path"
    recursive = "recursive"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.general import get_ssm_param_task

        self.module = get_ssm_param_task

        self.sut = self.module.GetSSMParamTask(
            parameter_name=self.parameter_name,
            name=self.name,
            default_value=self.default_value,
            region=self.region,
            path=self.path,
            recursive=self.recursive,
            depends_on=self.depends_on,
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
            spoke_account_id=self.spoke_account_id,
            spoke_region=self.spoke_region,
        )

        self.wire_up_mocks()

    def test_params_for_results_display(self):
        # setup
        expected_result = {
            "parameter_name": self.parameter_name,
            "name": self.name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

        # exercise
        actual_result = self.sut.params_for_results_display()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_no_exception_when_optional_parameters_are_missing(self):
        # setup
        # exercise
        self.module.GetSSMParamTask(
            parameter_name=self.parameter_name,
            name=self.name,
            default_value=self.default_value,
            region=self.region,
            path=self.path,
            recursive=self.recursive,
        )

    @skip
    def test_run(self):
        # setup
        # exercise
        actual_result = self.sut.run()

        # verify
        raise NotImplementedError()
