# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import cli_commands


def run(what="puppet", wait_for_completion=False):
    """
    Run something

    :param what: what should be run.  The only parameter that will work is ``puppet``
    :param wait_for_completion: Whether the command should wait for the completion of the pipeline before it returns
    """
    cli_commands.run(what, wait_for_completion)


def add_to_accounts(account_or_ou):
    """
    Add the parameter to the account list of the manifest file

    :param account_or_ou: A dict describing the the account or the ou to be added
    """
    cli_commands.add_to_accounts(account_or_ou)


def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    """
    remove the given ``account_id_or_ou_id_or_ou_path`` from the account list

    :param account_id_or_ou_id_or_ou_path: the value can be an account_id, ou_id or an ou_path.  It should be present \
    in the accounts list within the manifest file or an error is generated
    """
    cli_commands.remove_from_accounts(account_id_or_ou_id_or_ou_path)


def add_to_launches(launch_name, launch):
    """
    Add the given ``launch`` to the launches section using the given ``launch_name``

    :param launch_name: The launch name to use when adding the launch to the manifest launches
    :param launch: The dict to add to the launches
    """
    cli_commands.add_to_launches(launch_name, launch)


def remove_from_launches(launch_name):
    """
    remove the given ``launch_name`` from the launches list

    :param launch_name: The name of the launch to be removed from the launches section of the manifest file
    """
    cli_commands.remove_from_launches(launch_name)


def upload_config(config):
    """
    This function allows you to upload your configuration for puppet.  At the moment this should be a dict with an
    attribute named regions:
    regions: [
      'eu-west-3',
      'sa-east-1',
    ]

    :param config: The dict containing the configuration used for puppet
    """
    cli_commands.upload_config(config)


def bootstrap(with_manual_approvals):
    """
    Bootstrap the puppet account.  This will create the AWS CodeCommit repo containing the config and it will also
    create the AWS CodePipeline that will run the solution.

    :param with_manual_approvals: Boolean to specify whether there should be manual approvals before provisioning occurs
    """
    cli_commands.bootstrap(with_manual_approvals)


def bootstrap_spoke(puppet_account_id):
    """
    Bootstrap a spoke so that is can be used by the puppet account to share portfolios and provision products.  This
    must be run in the spoke account.

    :param puppet_account_id: this is the account id where you have installed aws-service-catalog-puppet
    """
    cli_commands.bootstrap_spoke(puppet_account_id)


def bootstrap_spoke_as(puppet_account_id, iam_role_arns):
    """
    Bootstrap a spoke so that it can be used by the puppet account to share portfolios and provision products.  This
    must be run in an account where you can assume the first ARN in the iam_role_arns list.

    :param puppet_account_id: this is the account id where you have installed aws-service-catalog-puppet
    :param iam_role_arns: this is a list of ARNs the function will assume (in order) before bootstrapping.  The final \
    ARN in the list should be the ARN of the spoke you want to bootstrap.
    """
    cli_commands.bootstrap_spoke_as(puppet_account_id, iam_role_arns)


def bootstrap_spokes_in_ou(ou_path_or_id, role_name, iam_role_arns):
    """
    Bootstrap each spoke in the given path or id

    :param ou_path_or_id: This is the ou path /example or the ou id for which you want each account bootstrapped
    :param role_name: This is the name (not ARN) of the IAM role to assume in each account when bootstrapping
    :param iam_role_arns: this is a list of ARNs the function will assume (in order) before bootstrapping.  The final \
    ARN in the list should be the ARN of account that can assume the role_name in the accounts to bootstrap.
    """
    cli_commands.bootstrap_spokes_in_ou(ou_path_or_id, role_name, iam_role_arns)
