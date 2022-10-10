#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import constants, config

import troposphere as t
from troposphere import iam

from servicecatalog_puppet.workflow.dependencies import tasks


class PrepareAccountForStackTask(tasks.TaskWithReference):
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "region": self.region,
            "account_id": self.account_id,
        }

    def run(self):
        puppet_version = constants.VERSION
        description = f"""Bootstrap template used to configure spoke account for stack use
                {{"version": "{puppet_version}", "framework": "servicecatalog-puppet", "role": "bootstrap-spoke-stack"}}"""

        template = t.Template(Description=description)

        template.add_resource(
            iam.Role(
                "PuppetStackRole",
                RoleName="PuppetStackRole",
                ManagedPolicyArns=[
                    t.Sub("arn:${AWS::Partition}:iam::aws:policy/AdministratorAccess")
                ],
                Path=config.get_puppet_role_path(),
                AssumeRolePolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["sts:AssumeRole"],
                            "Effect": "Allow",
                            "Principal": {"Service": ["cloudformation.amazonaws.com"]},
                        }
                    ],
                },
            )
        )

        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.create_or_update(
                StackName=constants.STACK_SPOKE_PREP_STACK_NAME,
                TemplateBody=template.to_yaml(),
                Capabilities=["CAPABILITY_NAMED_IAM"],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )

        self.write_output(self.params_for_results_display())
