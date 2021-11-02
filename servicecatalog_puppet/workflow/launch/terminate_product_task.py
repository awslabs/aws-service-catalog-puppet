#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.launch import do_terminate_product_task
from servicecatalog_puppet.workflow.launch import provisioning_task


class TerminateProductTask(
    provisioning_task.ProvisioningTask, dependency.DependenciesMixin
):
    launch_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    execution = luigi.Parameter()

    try_count = 1

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = {"section_dependencies": self.get_section_dependencies()}

        return requirements

    def run(self):
        yield do_terminate_product_task.DoTerminateProductTask(
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
        self.write_output(self.params_for_results_display())
