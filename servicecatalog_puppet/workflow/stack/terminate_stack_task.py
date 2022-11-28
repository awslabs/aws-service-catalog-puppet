#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import functools

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class TerminateStackTask(tasks.TaskWithReference):
    stack_name = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    bucket = luigi.Parameter()
    key = luigi.Parameter()
    version_id = luigi.Parameter()

    launch_name = luigi.Parameter()
    stack_set_name = luigi.Parameter()
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

    @property
    @functools.lru_cache(maxsize=32)
    def stack_name_to_use(self):
        if self.launch_name != "":
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
                stack_name = aws.get_stack_name_for_pp_id(servicecatalog, pp_id)
                return stack_name

        elif self.stack_set_name != "":
            with self.spoke_regional_client("cloudformation") as cloudformation:
                paginator = cloudformation.get_paginator("list_stacks")
                for page in paginator.paginate():
                    for summary in page.get("StackSummaries", []):
                        if summary.get("StackName").startswith(
                            f"StackSet-{self.stack_set_name}-"
                        ):
                            return summary.get("StackName")
                raise Exception(
                    f"Could not find a stack beginning with StackSet-{self.stack_set_name}- in {self.region} of {self.account_id}"
                )

        return self.stack_name

    def terminate_ssm_outputs(self):
        outputs = (
            self.get_from_manifest(constants.STACKS, self.stack_name)
            .get("outputs", {})
            .get("ssm", [])
        )
        for ssm_param_output in outputs:
            param_name = ssm_param_output.get("param_name")
            param_name = param_name.replace("${AWS::Region}", self.region)
            param_name = param_name.replace("${AWS::AccountId}", self.account_id)
            self.info(f"deleting SSM Param: {param_name}")
            with self.hub_client("ssm") as ssm:
                try:
                    ssm.delete_parameter(Name=param_name,)
                    self.info(f"deleting SSM Param: {param_name}")
                except ssm.exceptions.ParameterNotFound:
                    self.info(f"SSM Param: {param_name} not found")

    def run(self):
        if self.execution == constants.EXECUTION_MODE_HUB:
            self.terminate_ssm_outputs()

        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.ensure_deleted(StackName=self.stack_name_to_use)

        self.write_empty_output()
