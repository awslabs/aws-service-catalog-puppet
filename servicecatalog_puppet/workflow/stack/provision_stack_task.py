#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
import time
import functools

import cfn_tools
import luigi
from botocore.exceptions import ClientError

from servicecatalog_puppet import config
from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.stack import get_cloud_formation_template_from_s3
from servicecatalog_puppet.workflow.stack import provisioning_task
from servicecatalog_puppet.workflow.stack import prepare_account_for_stack_task


class ProvisionStackTask(
    provisioning_task.ProvisioningTask, dependency.DependenciesMixin
):
    stack_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    bucket = luigi.Parameter()
    key = luigi.Parameter()
    version_id = luigi.Parameter()

    launch_name = luigi.Parameter()
    stack_set_name = luigi.Parameter()
    capabilities = luigi.ListParameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    use_service_role = luigi.BoolParameter()

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
    def priority(self):
        return self.requested_priority

    def requires(self):
        requirements = {
            "section_dependencies": self.get_section_dependencies(),
            "ssm_params": self.get_parameters_tasks(),
            "template": get_cloud_formation_template_from_s3.GetCloudFormationTemplateFromS3(
                bucket=self.bucket,
                key=self.key,
                region=self.region,
                version_id=self.version_id,
                puppet_account_id=self.puppet_account_id,
                account_id=self.puppet_account_id,
            ),
        }
        if self.use_service_role:
            requirements[
                "prep"
            ] = prepare_account_for_stack_task.PrepareAccountForWorkspaceTask(
                account_id=self.account_id
            )

        return requirements

    def api_calls_used(self):
        apis = [
            f"servicecatalog.describe_stacks_{self.account_id}_{self.region}",
            f"servicecatalog.ensure_deleted_{self.account_id}_{self.region}",
            f"servicecatalog.get_template_summary_{self.account_id}_{self.region}",
            f"servicecatalog.get_template_{self.account_id}_{self.region}",
            f"servicecatalog.create_or_update_{self.account_id}_{self.region}",
        ]
        if self.launch_name != "":
            if "*" in self.launch_name:
                apis.append(
                    f"servicecatalog.scan_provisioned_products_{self.account_id}_{self.region}"
                )
            else:
                apis.append(
                    f"servicecatalog.describe_provisioned_product_{self.account_id}_{self.region}"
                )
        if self.stack_set_name != "":
            apis.append(f"cloudformation.list_stacks_{self.account_id}_{self.region}")

        if len(self.ssm_param_outputs) > 0:
            apis.append(f"ssm.put_parameter_and_wait")

        return apis

    @property
    @functools.lru_cache(maxsize=32)
    def stack_name_to_use(self):
        if self.launch_name != "":
            with self.spoke_regional_client("servicecatalog") as servicecatalog:
                if "*" in self.launch_name:
                    paginator = servicecatalog.get_paginator(
                        "scan_provisioned_products"
                    )
                    for page in paginator.paginate(
                        AccessLevelFilter={"Key": "Account", "Value": "self"},
                    ):
                        for provisioned_product in page.get("ProvisionedProducts", []):
                            name_as_a_regex = self.launch_name.replace("*", "(.*)")
                            if re.match(
                                name_as_a_regex, provisioned_product.get("Name")
                            ):
                                pp_stack_name = aws.get_stack_name_for_pp_id(
                                    servicecatalog, provisioned_product.get("Id")
                                )
                                return pp_stack_name

                    return self.stack_name
                else:
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
                    pp_stack_name = aws.get_stack_name_for_pp_id(servicecatalog, pp_id)
                    return pp_stack_name

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

    def ensure_stack_is_in_complete_status(self):
        current_stack = dict(StackStatus="DoesntExist")
        with self.spoke_regional_client("cloudformation") as cloudformation:
            try:
                paginator = cloudformation.get_paginator("describe_stacks")
                for page in paginator.paginate(StackName=self.stack_name_to_use,):
                    for stack in page.get("Stacks", []):
                        status = stack.get("StackStatus")
                        if status in [
                            "CREATE_IN_PROGRESS",
                            "ROLLBACK_IN_PROGRESS",
                            "DELETE_IN_PROGRESS",
                            "UPDATE_IN_PROGRESS",
                            "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
                            "UPDATE_ROLLBACK_IN_PROGRESS",
                            "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS",
                            "IMPORT_ROLLBACK_IN_PROGRESS",
                            "REVIEW_IN_PROGRESS",
                            "IMPORT_IN_PROGRESS",
                            "CREATE_FAILED",
                            "ROLLBACK_FAILED",
                            "DELETE_FAILED",
                            "UPDATE_ROLLBACK_FAILED",
                            "IMPORT_ROLLBACK_FAILED",
                        ]:
                            while status not in [
                                "ROLLBACK_COMPLETE",
                                "CREATE_COMPLETE",
                                "UPDATE_ROLLBACK_COMPLETE",
                                "DELETE_COMPLETE",
                                "UPDATE_COMPLETE",
                                "IMPORT_COMPLETE",
                                "IMPORT_ROLLBACK_COMPLETE",
                            ]:
                                time.sleep(5)
                                sub_paginator = cloudformation.get_paginator(
                                    "describe_stacks"
                                )
                                for sub_page in sub_paginator.paginate(
                                    StackName=stack.get("StackId"),
                                ):
                                    for sub_stack in sub_page.get("Stacks", []):
                                        status = sub_stack.get("StackStatus")
                            current_stack = stack
            except ClientError as error:
                if (
                    error.response["Error"]["Message"]
                    != f"Stack with id {self.stack_name_to_use} does not exist"
                ):
                    raise error
        return current_stack

    def run(self):
        stack = self.ensure_stack_is_in_complete_status()
        status = stack.get("StackStatus")

        with self.spoke_regional_client("cloudformation") as cloudformation:
            if status == "ROLLBACK_COMPLETE":
                if self.should_delete_rollback_complete_stacks:
                    cloudformation.ensure_deleted(StackName=self.stack_name_to_use)
                else:
                    raise Exception(
                        f"Stack: {self.stack_name_to_use} is in ROLLBACK_COMPLETE and need remediation"
                    )

        task_output = dict(
            **self.params_for_results_display(),
            account_parameters=tasks.unwrap(self.account_parameters),
            launch_parameters=tasks.unwrap(self.launch_parameters),
            manifest_parameters=tasks.unwrap(self.manifest_parameters),
        )

        all_params = self.get_parameter_values()

        template_to_provision_source = self.input().get("template").open("r").read()
        try:
            template_to_provision = cfn_tools.load_yaml(template_to_provision_source)
        except Exception:
            try:
                template_to_provision = cfn_tools.load_json(
                    template_to_provision_source
                )
            except Exception:
                raise Exception("Could not parse new template as YAML or JSON")

        params_to_use = dict()
        for param_name, p in template_to_provision.get("Parameters", {}).items():
            if all_params.get(param_name, p.get("DefaultValue")) is not None:
                params_to_use[param_name] = all_params.get(
                    param_name, p.get("DefaultValue")
                )

        existing_stack_params_dict = dict()
        existing_template = ""
        if status in [
            "CREATE_COMPLETE",
            "UPDATE_ROLLBACK_COMPLETE",
            "UPDATE_COMPLETE",
            "IMPORT_COMPLETE",
            "IMPORT_ROLLBACK_COMPLETE",
        ]:
            with self.spoke_regional_client("cloudformation") as cloudformation:
                existing_stack_params_dict = {}
                summary_response = cloudformation.get_template_summary(
                    StackName=self.stack_name_to_use,
                )
                for parameter in summary_response.get("Parameters"):
                    existing_stack_params_dict[
                        parameter.get("ParameterKey")
                    ] = parameter.get("DefaultValue")
                for stack_param in stack.get("Parameters", []):
                    existing_stack_params_dict[
                        stack_param.get("ParameterKey")
                    ] = stack_param.get("ParameterValue")
                template_body = cloudformation.get_template(
                    StackName=self.stack_name_to_use, TemplateStage="Original"
                ).get("TemplateBody")
                try:
                    existing_template = cfn_tools.load_yaml(template_body)
                except Exception:
                    try:
                        existing_template = cfn_tools.load_json(template_body)
                    except Exception:
                        raise Exception(
                            "Could not parse existing template as YAML or JSON"
                        )

        template_to_use = cfn_tools.dump_yaml(template_to_provision)
        if status == "UPDATE_ROLLBACK_COMPLETE":
            need_to_provision = True
        else:
            if existing_stack_params_dict == params_to_use:
                self.info(f"params unchanged")
                if template_to_use == cfn_tools.dump_yaml(existing_template):
                    self.info(f"template the same")
                    need_to_provision = False
                else:
                    self.info(f"template changed")
                    need_to_provision = True
            else:
                self.info(f"params changed")
                need_to_provision = True

        if need_to_provision:
            provisioning_parameters = []
            for p in params_to_use.keys():
                provisioning_parameters.append(
                    {"ParameterKey": p, "ParameterValue": params_to_use.get(p)}
                )
            with self.spoke_regional_client("cloudformation") as cloudformation:
                a = dict(
                    StackName=self.stack_name_to_use,
                    TemplateBody=template_to_use,
                    ShouldUseChangeSets=False,
                    Capabilities=self.capabilities,
                    Parameters=provisioning_parameters,
                    ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                    Tags=self.initialiser_stack_tags,
                )
                if self.use_service_role:
                    a["RoleARN"] = config.get_puppet_stack_role_arn(self.account_id)
                cloudformation.create_or_update(**a)

        task_output["provisioned"] = need_to_provision
        self.info(f"self.execution is {self.execution}")
        if self.execution in [
            constants.EXECUTION_MODE_HUB,
            constants.EXECUTION_MODE_SPOKE,
        ]:
            self.info(
                f"Running in execution mode: {self.execution}, checking for SSM outputs"
            )
            if len(self.ssm_param_outputs) > 0:
                with self.spoke_regional_client(
                    "cloudformation"
                ) as spoke_cloudformation:
                    stack_details = aws.get_stack_output_for(
                        spoke_cloudformation, self.stack_name_to_use,
                    )

                for ssm_param_output in self.ssm_param_outputs:
                    self.info(
                        f"writing SSM Param: {ssm_param_output.get('stack_output')}"
                    )
                    with self.hub_client("ssm") as ssm:
                        found_match = False
                        # TODO push into another task
                        for output in stack_details.get("Outputs", []):
                            if output.get("OutputKey") == ssm_param_output.get(
                                "stack_output"
                            ):
                                ssm_parameter_name = ssm_param_output.get("param_name")
                                ssm_parameter_name = ssm_parameter_name.replace(
                                    "${AWS::Region}", self.region
                                )
                                ssm_parameter_name = ssm_parameter_name.replace(
                                    "${AWS::AccountId}", self.account_id
                                )
                                found_match = True
                                ssm.put_parameter_and_wait(
                                    Name=ssm_parameter_name,
                                    Value=output.get("OutputValue"),
                                    Type=ssm_param_output.get("param_type", "String"),
                                    Overwrite=True,
                                )
                        if not found_match:
                            raise Exception(
                                f"[{self.uid}] Could not find match for {ssm_param_output.get('stack_output')}"
                            )

            self.write_output(task_output)
        else:
            self.write_output(task_output)
