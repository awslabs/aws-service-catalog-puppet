#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from servicecatalog_puppet import serialisation_utils

import cfn_tools
from botocore.exceptions import ClientError

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.stack import provision_stack_task


class ProvisionStackDryRunTask(provision_stack_task.ProvisionStackTask):
    def write_result(
        self, current_version, new_version, effect, current_status, active, notes=""
    ):
        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "current_version": current_version,
                        "new_version": new_version,
                        "effect": effect,
                        "current_status": current_status,
                        "active": active,
                        "notes": notes,
                        "params": self.param_kwargs,
                    },
                    indent=4,
                    default=str,
                )
            )

    def get_current_status(self):
        with self.spoke_regional_client("cloudformation") as cloudformation:
            try:
                paginator = cloudformation.get_paginator("describe_stacks")
                for page in paginator.paginate(StackName=self.stack_name,):
                    for stack in page.get("Stacks", []):
                        status = stack.get("StackStatus")
                        if status != "DELETE_COMPLETE":
                            return status
            except ClientError as error:
                if (
                    error.response["Error"]["Message"]
                    != f"Stack with id {self.stack_name} does not exist"
                ):
                    raise error
        return "-"

    def run(self):
        status = self.get_current_status()

        if status == "-":
            self.write_result(
                "-",
                self.version_id,
                effect=constants.CHANGE,
                current_status="-",
                active="N/A",
                notes="Stack would be created",
            )
        elif status == "ROLLBACK_COMPLETE":
            if self.should_delete_rollback_complete_stacks:
                self.write_result(
                    "-",
                    self.version_id,
                    effect=constants.CHANGE,
                    current_status="-",
                    active="N/A",
                    notes="Stack would be replaced",
                )
            else:
                self.write_result(
                    "-",
                    "-",
                    effect=constants.NO_CHANGE,
                    current_status="-",
                    active="N/A",
                    notes="Stack needs remediation - it's in ROLLBACK_COMPLETE",
                )
        else:
            task_output = dict(
                **self.params_for_results_display(),
                account_parameters=tasks.unwrap(self.account_parameters),
                launch_parameters=tasks.unwrap(self.launch_parameters),
                manifest_parameters=tasks.unwrap(self.manifest_parameters),
            )

            all_params = self.get_parameter_values()

            template_to_provision_source = self.input().get("template").open("r").read()
            try:
                template_to_provision = cfn_tools.load_yaml(
                    template_to_provision_source
                )
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
                    stack = cloudformation.describe_stacks(
                        StackName=self.stack_name
                    ).get("Stacks")[0]
                    summary_response = cloudformation.get_template_summary(
                        StackName=self.stack_name,
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
                        StackName=self.stack_name, TemplateStage="Original"
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
                self.write_result(
                    "?",
                    self.version_id,
                    effect=constants.CHANGE,
                    current_status=status,
                    active="N/A",
                    notes="Stack would be updated",
                )
            else:
                if existing_stack_params_dict == params_to_use:
                    self.info(f"params unchanged")
                    if template_to_use == cfn_tools.dump_yaml(existing_template):
                        self.info(f"template the same")
                        self.write_result(
                            "?",
                            self.version_id,
                            effect=constants.NO_CHANGE,
                            current_status=status,
                            active="N/A",
                            notes="No change",
                        )
                    else:
                        self.info(f"template changed")
                        self.write_result(
                            "?",
                            self.version_id,
                            effect=constants.CHANGE,
                            current_status=status,
                            active="N/A",
                            notes="Template has changed",
                        )
                else:
                    self.info(f"params changed")
                    self.write_result(
                        "?",
                        self.version_id,
                        effect=constants.CHANGE,
                        current_status=status,
                        active="N/A",
                        notes="Parameters have changed",
                    )
