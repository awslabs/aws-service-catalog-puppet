#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import logging

import click
from betterboto import client as betterboto_client
from jinja2 import Template

from servicecatalog_puppet import constants, asset_helpers

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def set_org_iam_role_arn(org_iam_role_arn):
    with betterboto_client.ClientContextManager("ssm") as ssm:
        ssm.put_parameter(
            Name=constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN,
            Type="String",
            Value=org_iam_role_arn,
            Overwrite=True,
        )
    click.echo("Uploaded config")


def bootstrap_org_master(puppet_account_id):
    with betterboto_client.ClientContextManager("cloudformation",) as cloudformation:
        org_iam_role_arn = None
        logger.info("Starting bootstrap of org master")
        stack_name = f"{constants.BOOTSTRAP_STACK_NAME}-org-master-{puppet_account_id}"
        template = asset_helpers.read_from_site_packages(
            f"{constants.BOOTSTRAP_STACK_NAME}-org-master.template.yaml"
        )
        template = Template(template).render(
            VERSION=constants.VERSION, puppet_account_id=puppet_account_id
        )
        args = {
            "StackName": stack_name,
            "TemplateBody": template,
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Parameters": [
                {
                    "ParameterKey": "PuppetAccountId",
                    "ParameterValue": str(puppet_account_id),
                },
                {
                    "ParameterKey": "Version",
                    "ParameterValue": constants.VERSION,
                    "UsePreviousValue": False,
                },
            ],
            "Tags": [{"Key": "ServiceCatalogPuppet:Actor", "Value": "Framework",}],
        }
        cloudformation.create_or_update(**args)
        response = cloudformation.describe_stacks(StackName=stack_name)
        if len(response.get("Stacks")) != 1:
            raise Exception("Expected there to be only one {} stack".format(stack_name))
        stack = response.get("Stacks")[0]

        for output in stack.get("Outputs"):
            if output.get("OutputKey") == constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN:
                logger.info("Finished bootstrap of org-master")
                org_iam_role_arn = output.get("OutputValue")

        if org_iam_role_arn is None:
            raise Exception(
                "Could not find output: {} in stack: {}".format(
                    constants.PUPPET_ORG_ROLE_FOR_EXPANDS_ARN, stack_name
                )
            )

    click.echo("Bootstrapped org master, org-iam-role-arn: {}".format(org_iam_role_arn))
