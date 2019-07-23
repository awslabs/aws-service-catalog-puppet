# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import cli_commands


def run(what, wait_for_completion):
    cli_commands.run(what, wait_for_completion)


def add_to_accounts(account_or_ou):
    cli_commands.add_to_accounts(account_or_ou)


def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    cli_commands.remove_from_accounts(account_id_or_ou_id_or_ou_path)


def add_to_launches(launch_name, launch):
    cli_commands.add_to_launches(launch_name, launch)


def remove_from_launches(launch_name):
    cli_commands.remove_from_launches(launch_name)
