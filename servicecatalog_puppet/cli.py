# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import click
import yaml

from servicecatalog_puppet import core


@click.group()
@click.option('--info/--no-info', default=False)
@click.option('--info-line-numbers/--no-info-line-numbers', default=False)
def cli(info, info_line_numbers):
    """cli for pipeline tools"""
    core.cli(info, info_line_numbers)


@cli.command()
@click.argument('f', type=click.File())
def generate_shares(f):
    core.generate_shares(f)


@cli.command()
@click.argument('f', type=click.File())
@click.option('--single-account', default=None)
@click.option('--num-workers', default=10)
def deploy(f, single_account, num_workers):
    core.deploy(f, single_account, num_workers)


@cli.command()
@click.argument('f', type=click.File())
@click.option('--single-account', default=None)
def graph(f, single_account):
    core.graph(f)


@cli.command()
@click.argument('f', type=click.File())
@click.option('--single-account', default=None)
def dry_run(f, single_account):
    core.deploy(f, single_account, is_dry_run=True)


@cli.command()
@click.argument('puppet_account_id')
@click.argument('iam_role_arns', nargs=-1)
@click.option('--permission-boundary', default="arn:aws:iam::aws:policy/AdministratorAccess")
def bootstrap_spoke_as(puppet_account_id, iam_role_arns, permission_boundary):
    core.bootstrap_spoke_as(puppet_account_id, iam_role_arns, permission_boundary)


@cli.command()
@click.argument('puppet_account_id')
@click.option('--permission-boundary', default="arn:aws:iam::aws:policy/AdministratorAccess")
def bootstrap_spoke(puppet_account_id, permission_boundary):
    core.bootstrap_spoke(puppet_account_id, permission_boundary)


@cli.command()
@click.argument('ou_path_or_id')
@click.argument('role_name')
@click.argument('iam_role_arns', nargs=-1)
@click.option('--permission-boundary', default="arn:aws:iam::aws:policy/AdministratorAccess")
@click.option('--num-workers', default=10)
def bootstrap_spokes_in_ou(ou_path_or_id, role_name, iam_role_arns, permission_boundary, num_workers):
    core.bootstrap_spokes_in_ou(ou_path_or_id, role_name, iam_role_arns, permission_boundary, num_workers)


@cli.command()
@click.argument('branch-name')
@click.option('--with-manual-approvals/--with-no-manual-approvals', default=False)
@click.option("--puppet-code-pipeline-role-permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--source-role-permissions-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--puppet-generate-role-permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--puppet-deploy-role-permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--puppet-provisioning-role-permissions-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--cloud-formation-deploy-role-permissions-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
def bootstrap_branch(
        branch_name,
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
):
    core.bootstrap_branch(
        branch_name,
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
    )


@cli.command()
@click.option('--with-manual-approvals/--with-no-manual-approvals', default=False)
@click.option("--puppet-code-pipeline-role-permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--source-role-permissions-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--puppet-generate-role-permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--puppet-deploy-role-permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--puppet-provisioning-role-permissions-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--cloud-formation-deploy-role-permissions-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess", show_default=True)
@click.option("--deploy_environment_compute_type", default="BUILD_GENERAL1_SMALL", show_default=True)
@click.option("--deploy_num_workers", default=10, type=click.INT ,show_default=True)
def bootstrap(
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type,
        deploy_num_workers,
):
    core.bootstrap(
        with_manual_approvals,
        puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary,
        puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type,
        deploy_num_workers,
    )


@cli.command()
@click.argument('complexity', default='simple')
@click.argument('p', type=click.Path(exists=True))
def seed(complexity, p):
    core.seed(complexity, p)


@cli.command()
@click.argument('expanded_manifest', type=click.File())
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
def list_launches(expanded_manifest, format):
    core.list_launches(expanded_manifest, format)


@cli.command()
@click.argument('f', type=click.File())
def expand(f):
    core.expand(f)


@cli.command()
@click.argument('f', type=click.File())
def validate(f):
    core.validate(f)


@cli.command()
def version():
    core.version()


@cli.command()
@click.argument('p', type=click.Path(exists=True))
def upload_config(p):
    content = open(p, 'r').read()
    config = yaml.safe_load(content)
    core.upload_config(config)


@cli.command()
@click.argument('org-iam-role-arn')
def set_org_iam_role_arn(org_iam_role_arn):
    core.set_org_iam_role_arn(org_iam_role_arn)


@cli.command()
@click.argument('puppet_account_id')
def bootstrap_org_master(puppet_account_id):
    core.bootstrap_org_master(puppet_account_id)


@cli.command()
@click.argument('what', default='puppet')
@click.option('--tail/--no-tail', default=False)
def run(what, tail):
    core.run(what, tail)


@cli.command()
def list_resources():
    core.list_resources()


@cli.command()
@click.argument('f', type=click.File())
@click.argument('name')
@click.argument('portfolio_name')
def import_product_set(f, name, portfolio_name):
    core.import_product_set(f, name, portfolio_name)


@cli.command()
@click.argument('account_or_ou_file_path', type=click.File())
def add_to_accounts(account_or_ou_file_path):
    core.add_to_accounts(
        yaml.safe_load(account_or_ou_file_path)
    )


@cli.command()
@click.argument('account_id_or_ou_id_or_ou_path')
def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    core.remove_from_accounts(account_id_or_ou_id_or_ou_path)


@cli.command()
@click.argument('launch_file_path', type=click.File())
def add_to_launches(launch_name, launch_file_path):
    core.add_to_launches(
        launch_name, yaml.safe_load(launch_file_path)
    )


@cli.command()
@click.argument('launch_name')
def remove_from_launches(launch_name):
    core.remove_from_launches(launch_name)


@cli.command()
@click.argument('f', type=click.File())
def reset_provisioned_product_owner(f):
    core.reset_provisioned_product_owner(f)


@cli.command()
@click.argument('regions', nargs=-1)
def set_regions(regions):
    core.set_config_value('regions', regions)


@cli.command()
@click.argument('name')
@click.argument('value')
def set_config_value(name, value, type=bool):
    core.set_config_value(name, value)


@cli.command()
@click.argument('execution_id')
def export_puppet_pipeline_logs(execution_id):
    core.export_puppet_pipeline_logs(execution_id)


@cli.command()
def uninstall():
    core.uninstall()


@cli.command()
def release_spoke():
    core.release_spoke()


if __name__ == "__main__":
    cli()
