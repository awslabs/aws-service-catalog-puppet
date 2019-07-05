# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import click

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
def bootstrap_branch(branch_name):
    cli_commands.bootstrap_branch(branch_name)


@cli.command()
def bootstrap():
    cli_commands.bootstrap()


@cli.command()
@click.argument('complexity', default='simple')
@click.argument('p', type=click.Path(exists=True))
def seed(complexity, p):
    cli_commands.seed(complexity, p)


@cli.command()
@click.argument('f', type=click.File())
def list_launches(f):
    cli_commands.list_launches(f)


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


if __name__ == "__main__":
    cli()
