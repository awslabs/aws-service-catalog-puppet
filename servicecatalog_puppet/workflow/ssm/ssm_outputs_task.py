#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier= Apache-2.0
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
import luigi

from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)
from servicecatalog_puppet.workflow.workspaces import Limits


class SSMOutputsTasks(tasks.PuppetTask):  # TODO add by path parameters
    # TODO add filter so this only works in hub and spoke modes
    puppet_account_id = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    task_reference = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()

    param_name = luigi.Parameter()
    stack_output = luigi.Parameter()
    task_generating_output = luigi.Parameter()
    force_operation = luigi.BoolParameter()

    dependencies_by_reference = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "account_id": self.account_id,
            "region": self.region,
            "param_name": self.param_name,
            "stack_output": self.stack_output,
            "force_operation": self.force_operation,
            "cache_invalidator": self.cache_invalidator,
        }

    def resources_used(self):
        uniq = f"{self.region}-{self.puppet_account_id}"
        return [
            (uniq, Limits.SSM_PUT_PARAMETER_PER_REGION_OF_ACCOUNT),
        ]

    def requires(self):
        return get_dependencies_for_task_reference(
            self.manifest_task_reference_file_path,
            self.task_reference,
            self.puppet_account_id,
        )

    def find_stack_output(
        self, generating_account_id, generating_region, generating_stack_name
    ):
        with self.cross_account_client(
            generating_account_id, "cloudformation", region_name=generating_region
        ) as cloudformation:
            response = cloudformation.describe_stacks(StackName=generating_stack_name,)
            for stack in response.get("Stacks", []):
                for output in stack.get("Outputs", []):
                    if output.get("OutputKey") == self.stack_output:
                        return output.get("OutputValue")

        raise Exception("Could not find stack output")

    def run(self):
        task_generating_output = self.load_from_input(self.task_generating_output)
        generating_account_id = task_generating_output.get("account_id")
        generating_region = task_generating_output.get("region")
        parameter_details = "Parameter not updated - stack/launch did not change and there was no force_operation"
        if task_generating_output.get("provisioned") or self.force_operation:
            if task_generating_output.get("section_name") == constants.STACKS:
                generating_stack_name = task_generating_output.get("stack_name_used")
                stack_output_value = self.find_stack_output(
                    generating_account_id, generating_region, generating_stack_name
                )
            elif task_generating_output.get("section_name") == constants.LAUNCHES:
                with self.cross_account_client(
                    generating_account_id,
                    "servicecatalog",
                    region_name=generating_region,
                ) as servicecatalog:
                    output = servicecatalog.get_provisioned_product_outputs(
                        ProvisionedProductName=task_generating_output.get(
                            "launch_name"
                        ),
                        OutputKeys=[self.stack_output],
                    ).get("Outputs")[0]
                    stack_output_value = output.get("OutputValue")
            else:
                raise Exception(
                    f"Unknown or not set section_name: {task_generating_output.get('section_name')}"
                )

            param_name_to_use = self.param_name.replace(
                "${AWS::Region}", self.region
            ).replace("${AWS::AccountId}", self.account_id)

            with self.spoke_regional_client("ssm") as ssm:
                parameter_details = ssm.put_parameter(
                    Name=param_name_to_use,
                    Value=stack_output_value,
                    Type="String",
                    Overwrite=True,
                )
        self.write_output(
            dict(
                task_generating_output=task_generating_output,
                parameter_details=parameter_details,
                **self.params_for_results_display(),
            )
        )
