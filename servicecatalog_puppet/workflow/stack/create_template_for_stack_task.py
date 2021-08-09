#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import troposphere as t
from troposphere import iam

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks


class CreateTemplateForStackTask(tasks.PuppetTask):
    def params_for_results_display(self):
        return {
            "cache_invalidator": self.cache_invalidator,
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

        self.write_output(template.to_yaml(), skip_json_dump=True)
