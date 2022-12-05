#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import functools
import re
import time

import cfn_tools
import luigi
from botocore.exceptions import ClientError

from servicecatalog_puppet import aws
from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.dependencies import tasks


class ProvisionStackTask(tasks.TaskWithParameters):
    stack_name = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    bucket = luigi.Parameter()
    key = luigi.Parameter()
    version_id = luigi.Parameter()

    launch_name = luigi.Parameter()
    stack_set_name = luigi.Parameter()
    get_s3_template_ref = luigi.Parameter()
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
    manifest_file_path = luigi.Parameter()

    tags = luigi.ListParameter()

    section_name = constants.STACKS

    @property
    def item_name(self):
        return self.stack_name

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
        waiting = "NotARealStatus"
        current_stack = dict(StackStatus=waiting)
        with self.spoke_regional_client("cloudformation") as cloudformation:
            while current_stack.get(
                "StackStatus"
            ) in constants.CLOUDFORMATION_IN_PROGRESS_STATUS + [waiting]:
                try:
                    stacks = cloudformation.describe_stacks(
                        StackName=self.stack_name_to_use
                    ).get("Stacks", [])
                    assert len(stacks) == 1
                    current_stack = stacks[0]

                    if (
                        current_stack.get("StackStatus")
                        in constants.CLOUDFORMATION_IN_PROGRESS_STATUS
                    ):
                        time.sleep(2)
                except ClientError as error:
                    if (
                        error.response["Error"]["Message"]
                        == f"Stack with id {self.stack_name} does not exist"
                    ):
                        return dict(StackStatus="NoStack")
                    else:
                        raise error

        if current_stack.get("StackStatus") in constants.CLOUDFORMATION_UNHAPPY_STATUS:
            raise Exception(
                f"stack {self.stack_name} is in state {current_stack.get('StackStatus')}"
            )

        return current_stack

    def run(self):
        stack = self.ensure_stack_is_in_complete_status()
        status = stack.get("StackStatus")

        if status != "NoStack":
            with self.spoke_regional_client("cloudformation") as cloudformation:
                if status == "ROLLBACK_COMPLETE":
                    if self.should_delete_rollback_complete_stacks:
                        cloudformation.ensure_deleted(StackName=self.stack_name_to_use)
                    else:
                        raise Exception(
                            f"Stack: {self.stack_name_to_use} is in ROLLBACK_COMPLETE and need remediation"
                        )

        task_output = dict(
            **self.params_for_results_display(), stack_name_used=self.stack_name_to_use,
        )

        all_params = self.get_parameter_values()

        template_to_provision_source = self.get_output_from_reference_dependency_raw(
            self.get_s3_template_ref
        )

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
        if status != "NoStack":
            if status in constants.CLOUDFORMATION_HAPPY_STATUS:
                with self.spoke_regional_client("cloudformation") as cloudformation:
                    summary_response = cloudformation.get_template_summary(
                        StackName=self.stack_name_to_use,
                    )
                    for parameter in summary_response.get("Parameters", []):
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
                    if isinstance(template_body, dict):
                        existing_template = template_body
                    else:
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
        if status in ["UPDATE_ROLLBACK_COMPLETE", "NoStack"]:
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
                if self.tags:
                    a["Tags"] = [
                        dict(Key=t.get("key"), Value=t.get("value")) for t in self.tags
                    ]
                cloudformation.create_or_update(**a)

        task_output["provisioned"] = need_to_provision
        task_output["section_name"] = self.section_name
        self.write_output(task_output)
