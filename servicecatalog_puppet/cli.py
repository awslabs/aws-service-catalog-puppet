# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import click
import yaml
import glob
import os
import re
import shutil

from servicecatalog_puppet import core, config, constants


@click.group()
@click.option("--info/--no-info", default=False)
@click.option("--info-line-numbers/--no-info-line-numbers", default=False)
def cli(info, info_line_numbers):
    """cli for pipeline tools"""
    core.cli(info, info_line_numbers)


@cli.command()
@click.argument("f", type=click.File())
@click.option("--single-account", default=None)
@click.option("--num-workers", default=10)
@click.option("--execution-mode", default="hub")
@click.option("--puppet-account-id", default=None)
@click.option("--home-region", default=None)
@click.option("--regions", default="")
@click.option("--should-collect-cloudformation-events", default=None, type=bool)
@click.option("--should-forward-events-to-eventbridge", default=None, type=bool)
@click.option("--should-forward-failures-to-opscenter", default=None, type=bool)
@click.option("--on-complete-url", default=None)
def deploy(
    f,
    single_account,
    num_workers,
    execution_mode,
    puppet_account_id,
    home_region,
    regions,
    should_collect_cloudformation_events,
    should_forward_events_to_eventbridge,
    should_forward_failures_to_opscenter,
    on_complete_url,
):
    click.echo(
        f"running in partition: {config.get_partition()} as {config.get_puppet_role_path()}{config.get_puppet_role_name()}"
    )
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    executor_account_id = config.get_current_account_id()

    if executor_account_id != puppet_account_id:
        click.echo("Not running in puppet account: writing config")
        with open("config.yaml", "w") as conf:
            conf.write(
                yaml.safe_dump(
                    dict(
                        home_region=home_region,
                        regions=regions.split(","),
                        should_collect_cloudformation_events=should_collect_cloudformation_events,
                        should_forward_events_to_eventbridge=should_forward_events_to_eventbridge,
                        should_forward_failures_to_opscenter=should_forward_failures_to_opscenter,
                    )
                )
            )
        core.deploy(
            f,
            puppet_account_id,
            executor_account_id,
            single_account=single_account,
            num_workers=num_workers,
            execution_mode=execution_mode,
            on_complete_url=on_complete_url,
        )
    else:
        if config.get_should_explode_manifest(puppet_account_id):
            click.echo("Using an exploded manifest")
            exploded_files = f.name.replace("expanded.yaml", "exploded-*.yaml")
            exploded_manifests = glob.glob(exploded_files)
            for exploded_manifest in exploded_manifests:
                click.echo(f"Created and running {exploded_manifest}")
                uid = re.search(".*exploded-(.*).yaml", exploded_manifest).group(1)
                open(f.name, "w").write(open(exploded_manifest, "r").read())
                core.deploy(
                    f,
                    puppet_account_id,
                    executor_account_id,
                    single_account=single_account,
                    num_workers=num_workers,
                    execution_mode=execution_mode,
                    on_complete_url=on_complete_url,
                    running_exploded=True,
                )
                output = f"exploded_results{os.path.sep}{uid}"
                os.makedirs(output)
                for d in ["results", "output", "data"]:
                    if os.path.exists(d):
                        shutil.move(d, f"{output}{os.path.sep}")

        else:
            core.deploy(
                f,
                puppet_account_id,
                executor_account_id,
                single_account=single_account,
                num_workers=num_workers,
                execution_mode=execution_mode,
                on_complete_url=on_complete_url,
            )


@cli.command()
@click.argument("f", type=click.File())
@click.option("--single-account", default=None)
def graph(f, single_account):
    core.graph(f)


@cli.command()
@click.argument("f", type=click.File())
@click.option("--single-account", default=None)
@click.option("--puppet-account-id", default=None)
def dry_run(f, single_account, puppet_account_id):
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    executor_account_id = config.get_current_account_id()
    core.deploy(
        f,
        executor_account_id,
        puppet_account_id,
        single_account=single_account,
        is_dry_run=True,
    )


@cli.command()
@click.argument("puppet_account_id")
@click.argument("iam_role_arns", nargs=-1)
@click.option(
    "--permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess"
)
@click.option("--puppet-role-name", default="PuppetRole")
@click.option("--puppet-role-path", default="/servicecatalog-puppet/")
def bootstrap_spoke_as(
    puppet_account_id,
    iam_role_arns,
    permission_boundary,
    puppet_role_name,
    puppet_role_path,
):
    core.bootstrap_spoke_as(
        puppet_account_id,
        iam_role_arns,
        permission_boundary,
        puppet_role_name,
        puppet_role_path,
    )


@cli.command()
@click.argument("puppet_account_id")
@click.option(
    "--permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess"
)
@click.option("--puppet-role-name", default="PuppetRole")
@click.option("--puppet-role-path", default="/servicecatalog-puppet/")
def bootstrap_spoke(
    puppet_account_id, permission_boundary, puppet_role_name, puppet_role_path
):
    core.bootstrap_spoke(
        puppet_account_id, permission_boundary, puppet_role_name, puppet_role_path
    )


@cli.command()
@click.argument("ou_path_or_id")
@click.argument("role_name")
@click.argument("iam_role_arns", nargs=-1)
@click.option(
    "--permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess"
)
@click.option("--num-workers", default=10)
@click.option("--puppet-role-name", default="PuppetRole")
@click.option("--puppet-role-path", default="/servicecatalog-puppet/")
def bootstrap_spokes_in_ou(
    ou_path_or_id,
    role_name,
    iam_role_arns,
    permission_boundary,
    num_workers,
    puppet_role_name,
    puppet_role_path,
):
    core.bootstrap_spokes_in_ou(
        ou_path_or_id,
        role_name,
        iam_role_arns,
        permission_boundary,
        num_workers,
        puppet_role_name,
        puppet_role_path,
    )


@cli.command()
@click.option("--with-manual-approvals/--with-no-manual-approvals", default=False)
@click.option(
    "--puppet-code-pipeline-role-permission-boundary",
    default="arn:aws:iam::aws:policy/AdministratorAccess",
    show_default=True,
    envvar="PUPPET_CODE_PIPELINE_ROLE_PERMISSION_BOUNDARY",
)
@click.option(
    "--source-role-permissions-boundary",
    default="arn:aws:iam::aws:policy/AdministratorAccess",
    show_default=True,
    envvar="SOURCE_ROLE_PERMISSIONS_BOUNDARY",
)
@click.option(
    "--puppet-generate-role-permission-boundary",
    default="arn:aws:iam::aws:policy/AdministratorAccess",
    show_default=True,
    envvar="PUPPET_GENERATE_ROLE_PERMISSION_BOUNDARY",
)
@click.option(
    "--puppet-deploy-role-permission-boundary",
    default="arn:aws:iam::aws:policy/AdministratorAccess",
    show_default=True,
    envvar="PUPPET_DEPLOY_ROLE_PERMISSION_BOUNDARY",
)
@click.option(
    "--puppet-provisioning-role-permissions-boundary",
    default="arn:aws:iam::aws:policy/AdministratorAccess",
    show_default=True,
    envvar="PUPPET_PROVISIONING_ROLE_PERMISSIONS_BOUNDARY",
)
@click.option(
    "--cloud-formation-deploy-role-permissions-boundary",
    default="arn:aws:iam::aws:policy/AdministratorAccess",
    show_default=True,
    envvar="CLOUD_FORMATION_DEPLOY_ROLE_PERMISSIONS_BOUNDARY",
)
@click.option(
    "--deploy_environment_compute_type",
    default="BUILD_GENERAL1_SMALL",
    show_default=True,
    envvar="DEPLOY_ENVIRONMENT_COMPUTE_TYPE",
)
@click.option(
    "--deploy_num_workers",
    default=10,
    type=click.INT,
    show_default=True,
    envvar="DEPLOY_NUM_WORKERS",
)
@click.option("--source-provider", default="CodeCommit", envvar="SCM_SOURCE_PROVIDER")
@click.option(
    "--repository_name", default="ServiceCatalogPuppet", envvar="SCM_REPOSITORY_NAME"
)
@click.option("--branch-name", default="master", envvar="SCM_BRANCH_NAME")
@click.option("--owner")
@click.option("--repo")
@click.option("--branch")
@click.option("--poll-for-source-changes/--no-poll-for-source-changes", default=True)
@click.option("--webhook-secret")
@click.option("--puppet-role-name", default="PuppetRole", envvar="PUPPET_ROLE_NAME")
@click.option(
    "--puppet-role-path", default="/servicecatalog-puppet/", envvar="PUPPET_ROLE_PATH"
)
@click.option("--scm-connection-arn", envvar="SCM_CONNECTION_ARN")
@click.option(
    "--scm-full-repository-id",
    default="ServiceCatalogFactory",
    envvar="SCM_FULL_REPOSITORY_ID",
)
@click.option("--scm-branch-name", default="main", envvar="SCM_BRANCH_NAME")
@click.option("--scm-bucket-name", envvar="SCM_BUCKET_NAME")
@click.option(
    "--scm-object-key", default="ServiceCatalogPuppet.zip", envvar="SCM_OBJECT_KEY"
)
@click.option(
    "--create-repo/--no-create-repo", default=False, envvar="SCM_SHOULD_CREATE_REPO"
)
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
    source_provider,
    repository_name,
    branch_name,
    owner,
    repo,
    branch,
    poll_for_source_changes,
    webhook_secret,
    puppet_role_name,
    puppet_role_path,
    scm_connection_arn,
    scm_full_repository_id,
    scm_branch_name,
    scm_bucket_name,
    scm_object_key,
    create_repo,
):
    puppet_account_id = config.get_puppet_account_id()

    parameters = dict(
        with_manual_approvals=with_manual_approvals,
        puppet_account_id=puppet_account_id,
        puppet_code_pipeline_role_permission_boundary=puppet_code_pipeline_role_permission_boundary,
        source_role_permissions_boundary=source_role_permissions_boundary,
        puppet_generate_role_permission_boundary=puppet_generate_role_permission_boundary,
        puppet_deploy_role_permission_boundary=puppet_deploy_role_permission_boundary,
        puppet_provisioning_role_permissions_boundary=puppet_provisioning_role_permissions_boundary,
        cloud_formation_deploy_role_permissions_boundary=cloud_formation_deploy_role_permissions_boundary,
        deploy_environment_compute_type=deploy_environment_compute_type,
        deploy_num_workers=deploy_num_workers,
        source_provider=source_provider,
        owner=None,
        repo=None,
        branch=None,
        poll_for_source_changes=poll_for_source_changes,
        webhook_secret=webhook_secret,
        puppet_role_name=puppet_role_name,
        puppet_role_path=puppet_role_path,
        scm_connection_arn=None,
        scm_full_repository_id=None,
        scm_branch_name=None,
        scm_bucket_name=None,
        scm_object_key=None,
        scm_skip_creation_of_repo=not create_repo,
    )
    if source_provider == "CodeCommit":
        parameters.update(dict(repo=repository_name, branch=branch_name,))
    elif source_provider == "GitHub":
        parameters.update(
            dict(owner=owner, repo=repo, branch=branch, webhook_secret=webhook_secret,)
        )
    elif source_provider == "CodeStarSourceConnection":
        parameters.update(
            dict(
                scm_connection_arn=scm_connection_arn,
                scm_full_repository_id=scm_full_repository_id,
                scm_branch_name=scm_branch_name,
            )
        )
    elif source_provider == "S3":
        parameters.update(
            dict(scm_bucket_name=scm_bucket_name, scm_object_key=scm_object_key,)
        )
    else:
        raise Exception(f"Unsupported source provider: {source_provider}")

    core.bootstrap(**parameters)


@cli.command()
@click.argument("complexity", default="simple")
@click.argument("p", type=click.Path(exists=True))
def seed(complexity, p):
    core.seed(complexity, p)


@cli.command()
@click.argument("expanded_manifest", type=click.File())
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def list_launches(expanded_manifest, format):
    current_account_id = puppet_account_id = config.get_puppet_account_id()
    core.deploy(
        expanded_manifest,
        puppet_account_id,
        current_account_id,
        single_account=None,
        is_dry_run=True,
        is_list_launches=format,
    )


@cli.command()
@click.argument("f", type=click.File())
@click.option("--single-account", default=None)
@click.option("--parameter-override-file", type=click.File())
@click.option(
    "--parameter-override-forced/--no-parameter-override-forced", default=False
)
def expand(f, single_account, parameter_override_file, parameter_override_forced):
    params = dict(single_account=single_account)
    if parameter_override_forced or core.is_a_parameter_override_execution():
        overrides = dict(**yaml.safe_load(parameter_override_file.read()))
        params.update(overrides)
        click.echo(f"Overridden parameters {params}")

    core.expand(f, **params)
    puppet_account_id = config.get_puppet_account_id()
    if config.get_should_explode_manifest(puppet_account_id):
        core.explode(f)


@cli.command()
@click.argument("f", type=click.File())
def validate(f):
    core.validate(f)


@cli.command()
def version():
    core.version()


@cli.command()
@click.argument("p", type=click.Path(exists=True))
def upload_config(p):
    content = open(p, "r").read()
    config = yaml.safe_load(content)
    core.upload_config(config)


@cli.command()
@click.argument("org-iam-role-arn")
def set_org_iam_role_arn(org_iam_role_arn):
    core.set_org_iam_role_arn(org_iam_role_arn)


@cli.command()
@click.argument("puppet_account_id")
def bootstrap_org_master(puppet_account_id):
    core.bootstrap_org_master(puppet_account_id)


@cli.command()
@click.argument("what", default="puppet")
@click.option("--tail/--no-tail", default=False)
def run(what, tail):
    core.run(what, tail)


@cli.command()
def list_resources():
    core.list_resources()


@cli.command()
@click.argument("f", type=click.File())
@click.argument("name")
@click.argument("portfolio_name")
def import_product_set(f, name, portfolio_name):
    core.import_product_set(f, name, portfolio_name)


@cli.command()
@click.argument("account_or_ou_file_path", type=click.File())
def add_to_accounts(account_or_ou_file_path):
    core.add_to_accounts(yaml.safe_load(account_or_ou_file_path))


@cli.command()
@click.argument("account_id_or_ou_id_or_ou_path")
def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    core.remove_from_accounts(account_id_or_ou_id_or_ou_path)


@cli.command()
@click.argument("launch_file_path", type=click.File())
def add_to_launches(launch_name, launch_file_path):
    core.add_to_launches(launch_name, yaml.safe_load(launch_file_path))


@cli.command()
@click.argument("launch_name")
def remove_from_launches(launch_name):
    core.remove_from_launches(launch_name)


@cli.command()
@click.argument("f", type=click.File())
def reset_provisioned_product_owner(f):
    core.reset_provisioned_product_owner(f)


@cli.command()
@click.argument("regions", nargs=-1)
def set_regions(regions):
    core.set_config_value("regions", regions)


@cli.command()
@click.argument("name")
@click.argument("value")
def set_config_value(name, value):
    core.set_config_value(name, value)


@cli.command()
@click.argument("name")
@click.argument("value")
def set_named_config_value(name, value):
    core.set_named_config_value(name, value)


@cli.command()
@click.argument("execution_id")
@click.option("--puppet-account-id", default=None)
def export_puppet_pipeline_logs(execution_id, puppet_account_id):
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    core.export_puppet_pipeline_logs(execution_id, puppet_account_id)


@cli.command()
@click.option("--puppet-account-id", default=None)
def uninstall(puppet_account_id):
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    core.uninstall(puppet_account_id)


@cli.command()
@click.option("--puppet-account-id", default=None)
def release_spoke(puppet_account_id):
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    core.release_spoke(puppet_account_id)


@cli.command()
@click.argument("iam_role_arns", nargs=-1)
def wait_for_code_build_in(iam_role_arns):
    core.wait_for_code_build_in(iam_role_arns)
    core.wait_for_cloudformation_in(iam_role_arns)
    click.echo("AWS CodeBuild is available")


@cli.command()
@click.option("--on-complete-url", default=None)
def wait_for_parameterised_run_to_complete(on_complete_url):
    click.echo("Starting to wait for parameterised run to complete")
    succeeded = core.wait_for_parameterised_run_to_complete(on_complete_url)
    click.echo(f"Finished: {'SUCCESS' if succeeded else 'FAILED'}")


if __name__ == "__main__":
    cli()
