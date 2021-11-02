#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.general import get_ssm_param_task
from servicecatalog_puppet.workflow.stack import provisioning_task
import functools


class TerminateStackTask(
    provisioning_task.ProvisioningTask,
    dependency.DependenciesMixin,
    get_ssm_param_task.PuppetTaskWithParameters,
):
    stack_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    bucket = luigi.Parameter()
    key = luigi.Parameter()
    version_id = luigi.Parameter()

    launch_name = luigi.Parameter()
    capabilities = luigi.ListParameter()

    use_service_role = luigi.BoolParameter()

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
            "stack_name": self.stack_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = {"section_dependencies": self.get_section_dependencies()}
        return requirements

    @property
    @functools.lru_cache(maxsize=32)
    def stack_name_to_use(self):
        if self.launch_name == "":
            return self.stack_name
        else:
            with self.spoke_regional_client("servicecatalog") as servicecatalog:
                try:
                    pp_id = (
                        servicecatalog.describe_provisioned_product(
                            Name=self.launch_name
                        )
                        .get("ProvisionedProductDetail")
                        .get("Id")
                    )
                except servicecatalog.exceptions.ResourceNotFoundException as e:
                    if (
                        "Provisioned product not found"
                        in e.response["Error"]["Message"]
                    ):
                        return self.stack_name
                    else:
                        raise e
                return f"SC-{self.account_id}-{pp_id}"

    def run(self):
        if self.execution == constants.EXECUTION_MODE_HUB:
            self.terminate_ssm_outputs()

        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.ensure_deleted(StackName=self.stack_name_to_use)

        self.write_output(self.params_for_results_display())
