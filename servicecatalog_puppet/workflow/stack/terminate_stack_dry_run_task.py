#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

from botocore.client import ClientError

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.stack import terminate_stack_task


class TerminateStackDryRunTask(terminate_stack_task.TerminateStackTask):
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
        current_status = self.get_current_status()

        if current_status == "-":
            self.write_result(
                "-",
                "-",
                effect=constants.NO_CHANGE,
                current_status=current_status,
                active="N/A",
                notes="Stack already deleted",
            )
        else:
            self.write_result(
                "?",
                "-",
                effect=constants.CHANGE,
                current_status=current_status,
                active="N/A",
                notes="Stack would be deleted",
            )

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
