#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import functools
import re

import luigi

from servicecatalog_puppet import aws, constants
from servicecatalog_puppet.workflow.dependencies import tasks


class SSMOutputsTasks(tasks.TaskWithReference):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    param_name = luigi.Parameter()
    stack_output = luigi.Parameter()
    task_generating_output = luigi.Parameter()
    task_generating_output_account_id = luigi.Parameter()
    task_generating_output_region = luigi.Parameter()
    task_generating_output_section_name = luigi.Parameter()
    task_generating_output_entity_name = luigi.Parameter()
    task_generating_output_stack_set_name = luigi.Parameter()
    task_generating_output_launch_name = luigi.Parameter()
    force_operation = luigi.BoolParameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
            "stack_output": self.stack_output,
            "force_operation": self.force_operation,
        }

    @property
    @functools.lru_cache(maxsize=32)
    def stack_name_to_use(self):
        if self.task_generating_output_launch_name != "":
            with self.cross_account_client(
                self.task_generating_output_account_id,
                "servicecatalog",
                region_name=self.task_generating_output_region,
            ) as servicecatalog:
                if "*" in self.task_generating_output_launch_name:
                    paginator = servicecatalog.get_paginator(
                        "scan_provisioned_products"
                    )
                    for page in paginator.paginate(
                        AccessLevelFilter={"Key": "Account", "Value": "self"},
                    ):
                        for provisioned_product in page.get("ProvisionedProducts", []):
                            name_as_a_regex = self.task_generating_output_launch_name.replace(
                                "*", "(.*)"
                            )
                            if re.match(
                                name_as_a_regex, provisioned_product.get("Name")
                            ):
                                pp_stack_name = aws.get_stack_name_for_pp_id(
                                    servicecatalog, provisioned_product.get("Id")
                                )
                                return pp_stack_name

                    return self.task_generating_output_entity_name
                else:
                    try:
                        pp_id = (
                            servicecatalog.describe_provisioned_product(
                                Name=self.task_generating_output_launch_name
                            )
                            .get("ProvisionedProductDetail")
                            .get("Id")
                        )
                    except servicecatalog.exceptions.ResourceNotFoundException as e:
                        if (
                            "Provisioned product not found"
                            in e.response["Error"]["Message"]
                        ):
                            return self.task_generating_output_entity_name
                        else:
                            raise e
                    pp_stack_name = aws.get_stack_name_for_pp_id(servicecatalog, pp_id)
                    return pp_stack_name

        elif self.task_generating_output_stack_set_name != "":
            with self.cross_account_client(
                self.task_generating_output_account_id,
                "cloudformation",
                region_name=self.task_generating_output_region,
            ) as cloudformation:
                paginator = cloudformation.get_paginator("list_stacks")
                for page in paginator.paginate():
                    for summary in page.get("StackSummaries", []):
                        if summary.get("StackName").startswith(
                            f"StackSet-{self.task_generating_output_stack_set_name}-"
                        ):
                            return summary.get("StackName")
                raise Exception(
                    f"Could not find a stack beginning with StackSet-{self.task_generating_output_stack_set_name}- in {self.task_generating_output_region} of {self.task_generating_output_account_id}"
                )

        return self.task_generating_output_entity_name

    def find_stack_output(self):
        with self.cross_account_client(
            self.task_generating_output_account_id,
            "cloudformation",
            region_name=self.task_generating_output_region,
        ) as cloudformation:
            response = cloudformation.describe_stacks(StackName=self.stack_name_to_use,)
            for stack in response.get("Stacks", []):
                for output in stack.get("Outputs", []):
                    if output.get("OutputKey") == self.stack_output:
                        return output.get("OutputValue")

        raise Exception("Could not find stack output")

    def get_ssm_parameter(self):
        with self.spoke_regional_client("ssm") as ssm:
            try:
                parameter = ssm.get_parameter(Name=self.param_name_to_use(),)
            except ssm.exceptions.ParameterNotFound:
                return None
            else:
                return parameter.get("Parameter")

    def run(self):
        existing_parameter = None
        if not self.force_operation:
            existing_parameter = self.get_ssm_parameter()
        parameter_details = "Parameter not updated - stack/launch did not change and there was no force_operation"
        if self.force_operation or existing_parameter is None:
            if self.task_generating_output_section_name == constants.STACKS:
                stack_output_value = self.find_stack_output()
            elif self.task_generating_output_section_name == constants.LAUNCHES:
                stack_output_value = self.find_launch_output()
            else:
                raise Exception(
                    f"Unknown or not set section_name: {self.task_generating_output_section_name}"
                )

            with self.spoke_regional_client("ssm") as ssm:
                parameter_details = ssm.put_parameter(
                    Name=self.param_name_to_use(),
                    Value=stack_output_value,
                    Type="String",
                    Overwrite=True,
                )
        else:
            stack_output_value = existing_parameter.get("Value")

        self.write_output(
            dict(
                # task_generating_output=task_generating_output,
                value=stack_output_value,
                parameter_details=parameter_details,
                **self.params_for_results_display(),
            )
        )

    @functools.lru_cache(maxsize=128)
    def param_name_to_use(self):
        return self.param_name.replace("${AWS::Region}", self.region).replace(
            "${AWS::AccountId}", self.account_id
        )

    def find_launch_output(self):
        with self.cross_account_client(
            self.task_generating_output_account_id,
            "servicecatalog",
            region_name=self.task_generating_output_region,
        ) as servicecatalog:
            output = servicecatalog.get_provisioned_product_outputs(
                ProvisionedProductName=self.task_generating_output_entity_name,
                OutputKeys=[self.stack_output],
            ).get("Outputs")[0]
            return output.get("OutputValue")


class TerminateSSMOutputsTasks(tasks.TaskWithReference):  # TODO add by path parameters
    # TODO add filter so this only works in hub and spoke modes
    puppet_account_id = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()

    param_name = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
        }

    cachable_level = constants.CACHE_LEVEL_RUN

    def run(self):
        param_name_to_use = self.param_name.replace(
            "${AWS::Region}", self.region
        ).replace("${AWS::AccountId}", self.account_id)

        with self.spoke_regional_client(
            "ssm"
        ) as ssm:  # TODO what happens when the param is deleted already
            try:
                parameter_details = ssm.delete_parameter(Name=param_name_to_use,)
                self.write_output(dict(parameter_details))
            except ssm.exceptions.ParameterNotFound:
                self.write_output(dict(result="parameter not found"))
