# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import click
import yaml

from servicecatalog_puppet import cli_commands


@click.group()
@click.option('--info/--no-info', default=False)
@click.option('--info-line-numbers/--no-info-line-numbers', default=False)
def cli(info, info_line_numbers):
    """cli for pipeline tools"""
    cli_commands.cli(info, info_line_numbers)


@cli.command()
@click.argument('f', type=click.File())
def generate_shares(f):
    cli_commands.generate_shares(f)


@cli.command()
@click.argument('f', type=click.File())
@click.option('--single-account', default=None)
def deploy(f, single_account):
    cli_commands.deploy(f, single_account)


@cli.command()
@click.argument('f', type=click.File())
def dry_run(f):
    cli_commands.dry_run(f)


@cli.command()
@click.argument('puppet_account_id')
@click.argument('iam_role_arns', nargs=-1)
def bootstrap_spoke_as(puppet_account_id, iam_role_arns):
    cli_commands.bootstrap_spoke_as(puppet_account_id, iam_role_arns)


@cli.command()
@click.argument('puppet_account_id')
def bootstrap_spoke(puppet_account_id):
    cli_commands.bootstrap_spoke(puppet_account_id)


@cli.command()
@click.argument('branch-name')
@click.option('--with-manual-approvals/--with-no-manual-approvals', default=False)
def bootstrap_branch(branch_name, with_manual_approvals):
    cli_commands.bootstrap_branch(branch_name, with_manual_approvals)


@cli.command()
@click.option('--with-manual-approvals/--with-no-manual-approvals', default=False)
def bootstrap(with_manual_approvals):
    cli_commands.bootstrap(with_manual_approvals)


@cli.command()
@click.argument('complexity', default='simple')
@click.argument('p', type=click.Path(exists=True))
def seed(complexity, p):
    cli_commands.seed(complexity, p)


@cli.command()
@click.argument('expanded_manifest', type=click.File())
@click.option('--format','-f', type=click.Choice(['table', 'json']),default='table')
def list_launches(expanded_manifest, format):
    cli_commands.list_launches(expanded_manifest, format)


@cli.command()
@click.argument('f', type=click.File())
def expand(f):
    cli_commands.expand(f)


@cli.command()
@click.argument('f', type=click.File())
def validate(f):
    cli_commands.validate(f)


@cli.command()
def version():
    cli_commands.version()


@cli.command()
@click.argument('p', type=click.Path(exists=True))
def upload_config(p):
    cli_commands.upload_config(p)


@cli.command()
@click.argument('org-iam-role-arn')
def set_org_iam_role_arn(org_iam_role_arn):
    cli_commands.set_org_iam_role_arn(org_iam_role_arn)


@cli.command()
@click.argument('puppet_account_id')
def bootstrap_org_master(puppet_account_id):
    cli_commands.bootstrap_org_master(puppet_account_id)


@cli.command()
def quick_start():
    cli_commands.quick_start()


@cli.command()
@click.argument('what', default='puppet')
@click.option('--tail/--no-tail', default=False)
def run(what, tail):
    cli_commands.run(what, tail)


@cli.command()
def list_resources():
    cli_commands.list_resources()


@cli.command()
@click.argument('f', type=click.File())
@click.argument('name')
@click.argument('portfolio_name')
def import_product_set(f, name, portfolio_name):
    cli_commands.import_product_set(f, name, portfolio_name)


@cli.command()
@click.argument('account_or_ou_file_path', type=click.File())
def add_to_accounts(account_or_ou_file_path):
    cli_commands.add_to_accounts(
        yaml.safe_load(account_or_ou_file_path)
    )


@cli.command()
@click.argument('account_id_or_ou_id_or_ou_path')
def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    cli_commands.remove_from_accounts(account_id_or_ou_id_or_ou_path)


@cli.command()
@click.argument('launch_file_path', type=click.File())
def add_to_launches(launch_name, launch_file_path):
    cli_commands.add_to_launches(
        launch_name, yaml.safe_load(launch_file_path)
    )


@cli.command()
@click.argument('launch_name')
def remove_from_launches(launch_name):
    cli_commands.remove_from_launches(launch_name)


@cli.command()
@click.argument('f', type=click.File())
def reset_provisioned_product_owner(f):
    cli_commands.reset_provisioned_product_owner(f)


if __name__ == "__main__":
    cli()
