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

    :param account_id_or_ou_id_or_ou_path: the value can be an account_id, ou_id or an ou_path.  It should be present in the
    accounts list within the manifest file or an error is generated
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
