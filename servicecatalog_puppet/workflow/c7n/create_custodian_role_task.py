#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi
import troposphere as t
from troposphere import iam

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow.dependencies import tasks


class CreateCustodianRoleTask(tasks.TaskWithReferenceAndCommonParameters):
    c7n_account_id = luigi.Parameter()
    role_name = luigi.Parameter()
    role_path = luigi.Parameter()
    role_managed_policy_arns = luigi.ListParameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
        }

    def run(self):
        c7n_account_id = self.c7n_account_id
        role_name = self.role_name
        role_path = self.role_path
        role_managed_policy_arns = self.role_managed_policy_arns

        tpl = t.Template()
        tpl.description = (
            "custodian role template for c7n created by service catalog puppet"
        )
        tpl.add_resource(
            iam.Role(
                role_name,
                RoleName=role_name,
                ManagedPolicyArns=[t.Sub(arn) for arn in role_managed_policy_arns],
                Path=role_path,
                AssumeRolePolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["sts:AssumeRole"],
                            "Effect": "Allow",
                            "Principal": {"Service": ["lambda.amazonaws.com"]},
                        },
                        {
                            "Action": ["sts:AssumeRole"],
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": t.Sub(
                                    "arn:${AWS::Partition}:iam::"
                                    + c7n_account_id
                                    + ":root"
                                )
                            },
                        },
                    ],
                },
            )
        )
        template = tpl.to_yaml()
        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.create_or_update(
                Capabilities=["CAPABILITY_NAMED_IAM"],
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-c7n-custodian",
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )
        self.write_empty_output()
