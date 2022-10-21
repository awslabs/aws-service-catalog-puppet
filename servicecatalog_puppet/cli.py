#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from servicecatalog_puppet import serialisation_utils
import os
import sys
from datetime import datetime

import click
import yaml

from servicecatalog_puppet import config, remote_config
from servicecatalog_puppet import constants
from servicecatalog_puppet import environmental_variables
from servicecatalog_puppet.commands import bootstrap as bootstrap_commands
from servicecatalog_puppet.commands import graph as graph_commands
from servicecatalog_puppet.commands import management as management_commands
from servicecatalog_puppet.commands import manifest as manifest_commands
from servicecatalog_puppet.commands import misc as misc_commands
from servicecatalog_puppet.commands import orgs as orgs_commands
from servicecatalog_puppet.commands import show_codebuilds as show_codebuilds_commands
from servicecatalog_puppet.commands import show_pipelines as show_pipelines_commands
from servicecatalog_puppet.commands import spoke_management as spoke_management_commands
from servicecatalog_puppet.commands import task_reference as task_reference_commands
from servicecatalog_puppet.commands import version as version_commands


@click.group()
@click.option("--info/--no-info", default=False)
@click.option("--info-line-numbers/--no-info-line-numbers", default=False)
def cli(info, info_line_numbers):
    """cli for pipeline tools"""
    misc_commands.cli(info, info_line_numbers)


@cli.command()
@click.argument("f", type=click.File())
def graph(f):
    click.echo(graph_commands.graph(f))


@cli.command()
@click.argument("f", type=click.File())
@click.option("--single-account", default=None)
@click.option("--puppet-account-id", default=None)
def dry_run(f, single_account, puppet_account_id):
    click.echo("This command is disabled for now, due to performance issues.")


def parse_tags(ctx, param, value):
    tags = list()
    for val in value:
        k, v = val.split("=")
        tags.append(dict(Key=k, Value=v))
    return tags


@cli.command()
@click.argument("puppet_account_id")
@click.argument("iam_role_arns", nargs=-1)
@click.option(
    "--permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess"
)
@click.option("--puppet-role-name", default="PuppetRole")
@click.option("--puppet-role-path", default="/servicecatalog-puppet/")
@click.option("--tag", multiple=True, callback=parse_tags, default=[])
def bootstrap_spoke_as(
    puppet_account_id,
    iam_role_arns,
    permission_boundary,
    puppet_role_name,
    puppet_role_path,
    tag,
):
    spoke_management_commands.bootstrap_spoke_as(
        puppet_account_id,
        iam_role_arns,
        permission_boundary,
        puppet_role_name,
        puppet_role_path,
        tag,
    )


@cli.command()
@click.argument("puppet_account_id")
@click.option(
    "--permission-boundary", default="arn:aws:iam::aws:policy/AdministratorAccess"
)
@click.option("--puppet-role-name", default="PuppetRole")
@click.option("--puppet-role-path", default="/servicecatalog-puppet/")
@click.option("--tag", multiple=True, callback=parse_tags, default=[])
def bootstrap_spoke(
    puppet_account_id, permission_boundary, puppet_role_name, puppet_role_path, tag
):
    spoke_management_commands.bootstrap_spoke(
        puppet_account_id, permission_boundary, puppet_role_name, puppet_role_path, tag
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
@click.option("--tag", multiple=True, callback=parse_tags, default=[])
def bootstrap_spokes_in_ou(
    ou_path_or_id,
    role_name,
    iam_role_arns,
    permission_boundary,
    num_workers,
    puppet_role_name,
    puppet_role_path,
    tag,
):
    setup_config()
    spoke_management_commands.bootstrap_spokes_in_ou(
        ou_path_or_id,
        role_name,
        iam_role_arns,
        permission_boundary,
        num_workers,
        puppet_role_name,
        puppet_role_path,
        tag,
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
    "--spoke_deploy_environment_compute_type",
    default="BUILD_GENERAL1_SMALL",
    show_default=True,
    envvar="SPOKE_DEPLOY_ENVIRONMENT_COMPUTE_TYPE",
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
@click.option(
    "--poll-for-source-changes/--no-poll-for-source-changes",
    default=True,
    envvar="SCT_POLL_FOR_SOURCE_CHANGES",
)
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
@click.option(
    "--should-validate/--no-should-validate",
    default=False,
    envvar="SCT_SHOULD_VALIDATE",
)
@click.option(
    "--custom-source-action-git-url", envvar="SCM_CUSTOM_SOURCE_ACTION_GIT_URL",
)
@click.option(
    "--custom-source-action-git-web-hook-ip-address",
    default="0.0.0.0/0",
    envvar="SCM_CUSTOM_SOURCE_ACTION_GIT_WEB_HOOK_IP_ADDRESS",
)
@click.option(
    "--custom-source-action-custom-action-type-version",
    default="CustomVersion1",
    envvar="SCM_CUSTOM_SOURCE_ACTION_CUSTOM_ACTION_TYPE_VERSION",
)
@click.option(
    "--custom-source-action-custom-action-type-provider",
    default="CustomProvider1",
    envvar="SCM_CUSTOM_SOURCE_ACTION_CUSTOM_ACTION_TYPE_PROVIDER",
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
    spoke_deploy_environment_compute_type,
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
    should_validate,
    custom_source_action_git_url,
    custom_source_action_git_web_hook_ip_address,
    custom_source_action_custom_action_type_version,
    custom_source_action_custom_action_type_provider,
):
    setup_config()
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
        spoke_deploy_environment_compute_type=spoke_deploy_environment_compute_type,
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
        should_validate=should_validate,
        custom_source_action_git_url=None,
        custom_source_action_git_web_hook_ip_address=None,
        custom_source_action_custom_action_type_version=None,
        custom_source_action_custom_action_type_provider=None,
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
    elif source_provider == "Custom":
        parameters.update(
            dict(
                custom_source_action_git_url=custom_source_action_git_url,
                branch=branch_name,
                custom_source_action_git_web_hook_ip_address=custom_source_action_git_web_hook_ip_address,
                custom_source_action_custom_action_type_version=custom_source_action_custom_action_type_version,
                custom_source_action_custom_action_type_provider=custom_source_action_custom_action_type_provider,
            )
        )
    else:
        raise Exception(f"Unsupported source provider: {source_provider}")

    bootstrap_commands.bootstrap(**parameters)


@cli.command()
@click.argument("complexity", default="simple")
@click.argument("p", type=click.Path(exists=True))
def seed(complexity, p):
    management_commands.seed(complexity, p)


@cli.command()
@click.argument("expanded_manifest", type=click.File())
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def list_launches(expanded_manifest, format):
    click.echo("This command is disabled for now, due to performance issues.")


@cli.command()
@click.argument("f", type=click.File())
@click.option("--single-account", default=None)
@click.option("--parameter-override-file", type=click.File())
@click.option(
    "--parameter-override-forced/--no-parameter-override-forced", default=False
)
def expand(f, single_account, parameter_override_file, parameter_override_forced):
    puppet_account_id = remote_config.get_puppet_account_id()
    regions = remote_config.get_regions(puppet_account_id, constants.HOME_REGION)
    extra_params = dict(single_account=None)
    if parameter_override_forced or misc_commands.is_a_parameter_override_execution():
        overrides = dict(**yaml.safe_load(parameter_override_file.read()))

        if overrides.get("subset"):
            subset = dict(**overrides.get("subset"))
        else:
            subset = dict(**overrides)

        if subset.get("single_account"):
            del subset["single_account"]

        if overrides.get("single_account"):
            del overrides["single_account"]

        extra_params = dict(
            single_account=overrides.get("single_account"), subset=subset
        )
        click.echo(f"Overridden parameters {extra_params}")

    manifest_commands.expand(f, puppet_account_id, regions, **extra_params)
    if config.get_should_explode_manifest(puppet_account_id):
        manifest_commands.explode(f)


@cli.command()
@click.argument("f", type=click.File())
def generate_task_reference(f,):
    setup_config()
    task_reference_commands.generate_task_reference(f)


def setup_config(
    puppet_account_id=None,
    single_account=None,
    execution_mode="hub",
    num_workers="10",
    home_region=None,
    regions="",
    should_collect_cloudformation_events="None",
    should_forward_events_to_eventbridge="None",
    should_forward_failures_to_opscenter="None",
    output_cache_starting_point="",
    is_caching_enabled="",
    global_sharing_mode_default="",
    on_complete_url=None,
):
    home_region_to_use = home_region or constants.HOME_REGION
    if puppet_account_id is None:
        puppet_account_id_to_use = remote_config.get_puppet_account_id()
    else:
        puppet_account_id_to_use = puppet_account_id
    os.environ[environmental_variables.PUPPET_ACCOUNT_ID] = puppet_account_id_to_use
    if single_account:
        os.environ[environmental_variables.SINGLE_ACCOUNT_ID] = single_account

    os.environ[environmental_variables.EXECUTION_MODE] = execution_mode
    os.environ[environmental_variables.NUM_WORKERS] = num_workers
    os.environ[environmental_variables.HOME_REGION] = home_region_to_use
    os.environ[environmental_variables.EXECUTOR_ACCOUNT_ID] = str(
        remote_config.get_current_account_id()
    )
    os.environ[environmental_variables.REGIONS] = json.dumps(
        regions
        if regions != ""
        else remote_config.get_regions(puppet_account_id_to_use, home_region_to_use)
    )
    if os.environ.get(environmental_variables.CACHE_INVALIDATOR):
        click.echo(
            f"Found existing {environmental_variables.CACHE_INVALIDATOR}: {os.environ.get(environmental_variables.CACHE_INVALIDATOR)}"
        )
    else:
        os.environ[environmental_variables.CACHE_INVALIDATOR] = str(datetime.now())

    os.environ[environmental_variables.SHOULD_USE_SNS] = (
        str(remote_config.get_should_use_sns(puppet_account_id_to_use, home_region))
        if should_collect_cloudformation_events == "None"
        else str(should_collect_cloudformation_events)
    )

    os.environ[environmental_variables.SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE] = str(
        str(
            remote_config.get_should_use_eventbridge(
                puppet_account_id_to_use, home_region
            )
        )
        if should_forward_events_to_eventbridge == "None"
        else should_forward_events_to_eventbridge
    )
    os.environ[environmental_variables.SHOULD_FORWARD_FAILURES_TO_OPSCENTER] = str(
        str(
            remote_config.get_should_forward_failures_to_opscenter(
                puppet_account_id_to_use, home_region
            )
        )
        if should_forward_failures_to_opscenter == "None"
        else should_forward_failures_to_opscenter
    )

    if not os.environ.get(environmental_variables.SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS):
        os.environ[environmental_variables.SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS] = str(
            remote_config.get_should_delete_rollback_complete_stacks(
                puppet_account_id_to_use
            )
        )

    if not os.environ.get(environmental_variables.SHOULD_USE_PRODUCT_PLANS):
        os.environ[environmental_variables.SHOULD_USE_PRODUCT_PLANS] = str(
            remote_config.get_should_use_product_plans(
                puppet_account_id_to_use, os.environ.get("AWS_DEFAULT_REGION")
            )
        )

    if not os.environ.get(environmental_variables.INITIALISER_STACK_TAGS):
        os.environ[
            environmental_variables.INITIALISER_STACK_TAGS
        ] = json.dumps(  # TODO make dynamic
            remote_config.get_initialiser_stack_tags()
        )

    os.environ[environmental_variables.VERSION] = constants.VERSION
    os.environ[
        environmental_variables.OUTPUT_CACHE_STARTING_POINT
    ] = output_cache_starting_point

    if is_caching_enabled == "":
        os.environ[environmental_variables.IS_CACHING_ENABLED] = str(
            remote_config.is_caching_enabled(puppet_account_id_to_use, home_region)
        )
    else:
        os.environ[environmental_variables.IS_CACHING_ENABLED] = str(is_caching_enabled)

    if global_sharing_mode_default == "":
        os.environ[
            environmental_variables.GLOBAL_SHARING_MODE
        ] = remote_config.get_global_sharing_mode_default(
            puppet_account_id_to_use, home_region
        )
    else:
        os.environ[
            environmental_variables.GLOBAL_SHARING_MODE
        ] = global_sharing_mode_default
    if on_complete_url:
        os.environ[environmental_variables.ON_COMPLETE_URL] = on_complete_url
    if not os.environ.get(environmental_variables.SPOKE_EXECUTION_MODE_DEPLOY_ENV):
        os.environ[
            environmental_variables.SPOKE_EXECUTION_MODE_DEPLOY_ENV
        ] = remote_config.get_spoke_deploy_environment_compute_type(
            puppet_account_id_to_use, home_region
        )


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--num-workers", default=10)
@click.option("--execution-mode", default="hub")
@click.option("--puppet-account-id", default=None)
@click.option("--single-account", default=None)
@click.option("--home-region", default=None)
@click.option("--regions", default="")
@click.option("--should-collect-cloudformation-events", default=None, type=bool)
@click.option("--should-forward-events-to-eventbridge", default=None, type=bool)
@click.option("--should-forward-failures-to-opscenter", default=None, type=bool)
@click.option(
    "--output-cache-starting-point",
    default="",
    show_default=True,
    envvar="OUTPUT_CACHE_STARTING_POINT",
)
@click.option(
    "--is-caching-enabled", default="", envvar="SCT_IS_CACHING_ENABLED",
)
@click.option("--parameter-override-file", type=click.File())
@click.option(
    "--parameter-override-forced/--no-parameter-override-forced", default=False
)
@click.option("--on-complete-url", default=None)
def deploy_from_task_reference(
    path,
    num_workers,
    execution_mode,
    puppet_account_id,
    single_account,
    home_region,
    regions,
    should_collect_cloudformation_events,
    should_forward_events_to_eventbridge,
    should_forward_failures_to_opscenter,
    output_cache_starting_point,
    is_caching_enabled,
    parameter_override_file,
    parameter_override_forced,
    on_complete_url,
):
    params = dict()
    if parameter_override_forced or misc_commands.is_a_parameter_override_execution():
        overrides = dict(**yaml.safe_load(parameter_override_file.read()))
        if overrides.get("subset"):
            subset = overrides.get("subset")
            overrides = dict(
                section=subset.get("section"),
                item=subset.get("name"),
                include_dependencies=subset.get("include_dependencies"),
                include_reverse_dependencies=subset.get("include_reverse_dependencies"),
            )
        params.update(
            dict(single_account=overrides.get("single_account"), subset=overrides,)
        )
        click.echo(f"Overridden parameters {params}")

    setup_config(
        puppet_account_id=puppet_account_id,
        single_account=single_account or params.get("single_account"),
        num_workers=str(num_workers),
        execution_mode=execution_mode,
        home_region=home_region,
        regions=regions,
        should_collect_cloudformation_events=str(should_collect_cloudformation_events),
        should_forward_events_to_eventbridge=str(should_forward_events_to_eventbridge),
        should_forward_failures_to_opscenter=str(should_forward_failures_to_opscenter),
        output_cache_starting_point=output_cache_starting_point,
        is_caching_enabled=is_caching_enabled,
        on_complete_url=on_complete_url,
    )

    click.echo(
        f"running in partition: {config.get_partition()} as {config.get_puppet_role_path()}{config.get_puppet_role_name()}"
    )

    task_reference_commands.deploy_from_task_reference(path)


@cli.command()
@click.argument("p", type=click.Path())
@click.option("--num-workers", default=10)
@click.option("--execution-mode", default="hub")
@click.option("--puppet-account-id")
@click.option("--single-account", default=None)
@click.option("--home-region", default=None)
@click.option("--regions", default="")
@click.option("--should-collect-cloudformation-events", default=None, type=bool)
@click.option("--should-forward-events-to-eventbridge", default=None, type=bool)
@click.option("--should-forward-failures-to-opscenter", default=None, type=bool)
@click.option(
    "--output-cache-starting-point",
    default="",
    show_default=True,
    envvar="OUTPUT_CACHE_STARTING_POINT",
)
@click.option(
    "--is-caching-enabled", default="", envvar="SCT_IS_CACHING_ENABLED",
)
@click.option(
    "--global-sharing-mode-default", default="", envvar="SCT_GLOBAL_SHARING_MODE",
)
def deploy_in_spoke_from_task_reference(
    p,
    num_workers,
    execution_mode,
    puppet_account_id,
    single_account,
    home_region,
    regions,
    should_collect_cloudformation_events,
    should_forward_events_to_eventbridge,
    should_forward_failures_to_opscenter,
    output_cache_starting_point,
    is_caching_enabled,
    global_sharing_mode_default,
):
    setup_config(
        puppet_account_id=puppet_account_id,
        single_account=single_account,
        num_workers=str(num_workers),
        execution_mode=execution_mode,
        home_region=home_region,
        regions=regions,
        should_collect_cloudformation_events=str(should_collect_cloudformation_events),
        should_forward_events_to_eventbridge=str(should_forward_events_to_eventbridge),
        should_forward_failures_to_opscenter=str(should_forward_failures_to_opscenter),
        output_cache_starting_point=output_cache_starting_point,
        is_caching_enabled=is_caching_enabled,
        global_sharing_mode_default=global_sharing_mode_default,
    )
    click.echo(
        f"running in partition: {config.get_partition()} as {config.get_puppet_role_path()}{config.get_puppet_role_name()}"
    )

    task_reference_commands.deploy_from_task_reference(p)


@cli.command()
@click.argument("f", type=click.File())
def validate(f):
    setup_config()
    manifest_commands.validate(f)


@cli.command()
def version():
    setup_config()
    version_commands.version()


@cli.command()
@click.option(
    "--filter", type=click.Choice(["none", "single-runs", "full-runs"]), default="none"
)
@click.option("--format", type=click.Choice(["csv", "json"]), default="csv")
@click.option("--limit", type=click.INT, default=20)
def show_codebuilds(filter, format, limit):
    setup_config()
    show_codebuilds_commands.show_codebuilds(filter, limit, format)


@cli.command()
@click.argument("p", type=click.Path(exists=True))
def upload_config(p):
    setup_config()
    content = open(p, "r").read()
    management_commands.upload_config(yaml.safe_load(content))


@cli.command()
@click.argument("org-iam-role-arn")
def set_org_iam_role_arn(org_iam_role_arn):
    setup_config()
    orgs_commands.set_org_iam_role_arn(org_iam_role_arn)


@cli.command()
@click.argument("org-iam-role-arn")
def set_org_scp_role_arn(org_iam_role_arn):
    setup_config()
    orgs_commands.set_org_scp_role_arn(org_iam_role_arn)


@cli.command()
@click.argument("puppet_account_id")
@click.option("--tag", multiple=True, callback=parse_tags, default=[])
def bootstrap_org_master(puppet_account_id, tag):
    setup_config()
    orgs_commands.bootstrap_org_master(puppet_account_id, tag)


@cli.command()
@click.argument("puppet_account_id")
@click.option("--tag", multiple=True, callback=parse_tags, default=[])
def bootstrap_scp_master(puppet_account_id, tag):
    setup_config()
    orgs_commands.bootstrap_scp_master(puppet_account_id, tag)


@cli.command()
@click.argument("what", default="puppet")
@click.option("--tail/--no-tail", default=False)
def run(what, tail):
    setup_config()
    misc_commands.run(what, tail)


@cli.command()
def list_resources():
    setup_config()
    management_commands.list_resources()


@cli.command()
@click.argument("f", type=click.File())
@click.argument("name")
@click.argument("portfolio_name")
def import_product_set(f, name, portfolio_name):
    setup_config()
    manifest_commands.import_product_set(f, name, portfolio_name)


@cli.command()
@click.argument("account_or_ou_file_path", type=click.File())
def add_to_accounts(account_or_ou_file_path):
    setup_config()
    manifest_commands.add_to_accounts(yaml.safe_load(account_or_ou_file_path))


@cli.command()
@click.argument("account_id_or_ou_id_or_ou_path")
def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    setup_config()
    manifest_commands.remove_from_accounts(account_id_or_ou_id_or_ou_path)


@cli.command()
@click.argument("launch_file_path", type=click.File())
def add_to_launches(launch_name, launch_file_path):
    setup_config()
    manifest_commands.add_to_launches(launch_name, yaml.safe_load(launch_file_path))


@cli.command()
@click.argument("launch_name")
def remove_from_launches(launch_name):
    setup_config()
    manifest_commands.remove_from_launches(launch_name)


@cli.command()
@click.argument("f", type=click.File())
def reset_provisioned_product_owner(f):
    raise Exception(
        "This is not supported within this version, please try an older version"
    )


@cli.command()
@click.argument("regions", nargs=-1)
def set_regions(regions):
    management_commands.set_config_value("regions", regions)


@cli.command()
@click.argument("name")
@click.argument("value")
def set_config_value(name, value):
    is_a_boolean = dict(spoke_deploy_environment_compute_type=False).get(name, True)
    management_commands.set_config_value(name, value, is_a_boolean)


@cli.command()
@click.argument("name")
@click.argument("value")
def set_named_config_value(name, value):
    management_commands.set_named_config_value(name, value)


@cli.command()
@click.argument("execution_id")
@click.option("--puppet-account-id", default=None)
def export_puppet_pipeline_logs(execution_id, puppet_account_id):
    setup_config(puppet_account_id=puppet_account_id)
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    management_commands.export_puppet_pipeline_logs(execution_id, puppet_account_id)


@cli.command()
@click.argument("codebuild_execution_id")
@click.option("--puppet-account-id", default=None)
@click.option("--group-by-pid/--no-group-by-pid", default=False)
def generate_deploy_viz(codebuild_execution_id, puppet_account_id, group_by_pid):
    setup_config(puppet_account_id=puppet_account_id)
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    management_commands.export_deploy_viz(
        codebuild_execution_id, group_by_pid, puppet_account_id
    )


@cli.command()
@click.argument("codebuild_execution_id")
@click.option("--puppet-account-id", default=None)
def export_traces(codebuild_execution_id, puppet_account_id):
    setup_config(puppet_account_id=puppet_account_id)
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    management_commands.export_traces(codebuild_execution_id, puppet_account_id)


@cli.command()
@click.option("--puppet-account-id", default=None)
def uninstall(puppet_account_id):
    setup_config(puppet_account_id=puppet_account_id)
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    misc_commands.uninstall(puppet_account_id)


@cli.command()
@click.option("--puppet-account-id", default=None)
def release_spoke(puppet_account_id):
    setup_config(puppet_account_id=puppet_account_id)
    if puppet_account_id is None:
        puppet_account_id = config.get_puppet_account_id()
    spoke_management_commands.release_spoke(puppet_account_id)


@cli.command()
@click.argument("iam_role_arns", nargs=-1)
def wait_for_code_build_in(iam_role_arns):
    misc_commands.wait_for_code_build_in(iam_role_arns)
    misc_commands.wait_for_cloudformation_in(iam_role_arns)
    click.echo("AWS CodeBuild is available")


@cli.command()
@click.option("--on-complete-url", default=None)
def wait_for_parameterised_run_to_complete(on_complete_url):
    setup_config(puppet_account_id=remote_config.get_puppet_account_id())
    click.echo("Starting to wait for parameterised run to complete")
    succeeded = misc_commands.wait_for_parameterised_run_to_complete(on_complete_url)
    if succeeded:
        click.echo(f"Finished: 'SUCCESS'")
        sys.exit(0)
    else:
        click.echo(f"Finished: 'FAILED'")
        sys.exit(1)


@cli.command()
@click.option(
    "--format", "-f", type=click.Choice(["table", "json", "html"]), default="table"
)
def show_pipelines(format):
    show_pipelines_commands.show_pipelines(format)


if __name__ == "__main__":
    cli()
