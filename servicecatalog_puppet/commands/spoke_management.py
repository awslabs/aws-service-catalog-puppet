#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import logging

import click
from betterboto import client as betterboto_client
from jinja2 import Template

from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import (
    management as management_tasks,
    runner as runner,
)

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def _do_bootstrap_spoke(
    puppet_account_id,
    cloudformation,
    permission_boundary,
    puppet_role_name,
    puppet_role_path,
):
    template = asset_helpers.read_from_site_packages(
        "{}-spoke.template.yaml".format(constants.BOOTSTRAP_STACK_NAME)
    )
    template = Template(template).render(VERSION=constants.VERSION)
    args = {
        "StackName": "{}-spoke".format(constants.BOOTSTRAP_STACK_NAME),
        "TemplateBody": template,
        "Capabilities": ["CAPABILITY_NAMED_IAM"],
        "Parameters": [
            {
                "ParameterKey": "PuppetAccountId",
                "ParameterValue": str(puppet_account_id),
            },
            {
                "ParameterKey": "PermissionBoundary",
                "ParameterValue": permission_boundary,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "Version",
                "ParameterValue": constants.VERSION,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetRoleName",
                "ParameterValue": puppet_role_name,
                "UsePreviousValue": False,
            },
            {
                "ParameterKey": "PuppetRolePath",
                "ParameterValue": puppet_role_path,
                "UsePreviousValue": False,
            },
        ],
        "Tags": [{"Key": "ServiceCatalogPuppet:Actor", "Value": "Framework",}],
    }
    cloudformation.create_or_update(**args)
    logger.info("Finished bootstrap of spoke")


def bootstrap_spoke_as(
    puppet_account_id,
    iam_role_arns,
    permission_boundary,
    puppet_role_name,
    puppet_role_path,
):
    cross_accounts = []
    index = 0
    for role in iam_role_arns:
        cross_accounts.append((role, "bootstrapping-role-{}".format(index)))
        index += 1

    with betterboto_client.CrossMultipleAccountsClientContextManager(
        "cloudformation", cross_accounts
    ) as cloudformation:
        _do_bootstrap_spoke(
            puppet_account_id,
            cloudformation,
            permission_boundary,
            puppet_role_name,
            puppet_role_path,
        )


def bootstrap_spoke(
    puppet_account_id, permission_boundary, puppet_role_name, puppet_role_path
):
    with betterboto_client.ClientContextManager("cloudformation") as cloudformation:
        _do_bootstrap_spoke(
            puppet_account_id,
            cloudformation,
            permission_boundary,
            puppet_role_name,
            puppet_role_path,
        )


def release_spoke(puppet_account_id):
    with betterboto_client.ClientContextManager(
        "cloudformation", region_name=config.get_home_region(puppet_account_id)
    ) as cloudformation:
        cloudformation.ensure_deleted(
            StackName=f"{constants.BOOTSTRAP_STACK_NAME}-spoke"
        )


def bootstrap_spokes_in_ou(
    ou_path_or_id,
    role_name,
    iam_role_arns,
    permission_boundary,
    num_workers,
    puppet_role_name,
    puppet_role_path,
):
    puppet_account_id = config.get_puppet_account_id()
    org_iam_role_arn = config.get_org_iam_role_arn(puppet_account_id)
    if org_iam_role_arn is None:
        click.echo("No org role set - not expanding")
    else:
        click.echo("Expanding using role: {}".format(org_iam_role_arn))
        with betterboto_client.CrossAccountClientContextManager(
            "organizations", org_iam_role_arn, "org-iam-role"
        ) as client:
            tasks = []
            if ou_path_or_id.startswith("/"):
                ou_id = client.convert_path_to_ou(ou_path_or_id)
            else:
                ou_id = ou_path_or_id
            logging.info(f"ou_id is {ou_id}")
            response = client.list_children_nested(ParentId=ou_id, ChildType="ACCOUNT")
            for spoke in response:
                tasks.append(
                    management_tasks.BootstrapSpokeAsTask(
                        puppet_account_id=puppet_account_id,
                        account_id=spoke.get("Id"),
                        iam_role_arns=iam_role_arns,
                        role_name=role_name,
                        permission_boundary=permission_boundary,
                        puppet_role_name=puppet_role_name,
                        puppet_role_path=puppet_role_path,
                    )
                )

        runner.run_tasks_for_bootstrap_spokes_in_ou(tasks, num_workers)
