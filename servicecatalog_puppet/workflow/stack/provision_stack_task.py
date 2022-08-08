#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
import time
import functools

import cfn_tools
import luigi
from botocore.exceptions import ClientError

from servicecatalog_puppet import yaml_utils

from servicecatalog_puppet import config
from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.stack import get_cloud_formation_template_from_s3
from servicecatalog_puppet.workflow.stack import provisioning_task
from servicecatalog_puppet.workflow.stack import prepare_account_for_stack_task
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)


class ProvisionStackTask(
    provisioning_task.ProvisioningTask, dependency.DependenciesMixin
):
    task_reference = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

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
        reference_dependencies = get_dependencies_for_task_reference(
            self.manifest_task_reference_file_path,
            self.task_reference,
            self.puppet_account_id,
        )

        requirements = {
            "reference_dependencies": reference_dependencies,
            "template": get_cloud_formation_template_from_s3.GetCloudFormationTemplateFromS3(
                bucket=self.bucket,
                key=self.key,
                region=self.region,
                version_id=self.version_id,
                puppet_account_id=self.puppet_account_id,
                account_id=self.puppet_account_id,
            ),
        }
        #     #TODO rename the task class name! fixme
        #     if self.use_service_role:
        #         requirements[
        #             "prep"
        #         ] = prepare_account_for_stack_task.PrepareAccountForWorkspaceTask(
        #             account_id=self.account_id
        #         )
        #
        return requirements

    def api_calls_used(self):
        # TODO fixme
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
        self.info(111111)
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

        self.info(222222)
        task_output = dict(
            **self.params_for_results_display(), stack_name_used=self.stack_name_to_use,
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

        self.info(333333333)
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
        self.info(444444444)
        if status in ["UPDATE_ROLLBACK_COMPLETE", "NoStack"]:
            need_to_provision = True
        else:
            print(f"existing_stack_params_dict is {existing_stack_params_dict}")
            print(f"params_to_use is {params_to_use}")
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

        self.info(555555555555)
        self.info(6666666666)
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
        task_output["section_name"] = self.section_name
        self.info(7777777777)
        self.write_output(task_output)
