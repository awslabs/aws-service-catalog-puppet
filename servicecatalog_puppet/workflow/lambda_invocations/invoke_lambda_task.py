#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.lambda_invocations import do_invoke_lambda_task
from servicecatalog_puppet.workflow.lambda_invocations import (
    lambda_invocation_base_task,
)
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class InvokeLambdaTask(
    lambda_invocation_base_task.LambdaInvocationBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    lambda_invocation_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    function_name = luigi.Parameter()
    qualifier = luigi.Parameter()
    invocation_type = luigi.Parameter()

    execution = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    launch_parameters = luigi.DictParameter()
    manifest_parameters = luigi.DictParameter()
    account_parameters = luigi.DictParameter()

    all_params = []

    manifest_file_path = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = {"section_dependencies": self.get_section_dependencies()}
        return requirements

    def run(self):
        yield do_invoke_lambda_task.DoInvokeLambdaTask(
            lambda_invocation_name=self.lambda_invocation_name,
            region=self.region,
            account_id=self.account_id,
            function_name=self.function_name,
            qualifier=self.qualifier,
            invocation_type=self.invocation_type,
            puppet_account_id=self.puppet_account_id,
            launch_parameters=self.launch_parameters,
            manifest_parameters=self.manifest_parameters,
            account_parameters=self.account_parameters,
            manifest_file_path=self.manifest_file_path,
        )
        self.write_output(self.params_for_results_display())
