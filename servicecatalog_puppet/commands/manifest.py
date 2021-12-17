#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import logging

import click
import requests
import yamale
import yaml
from betterboto import client as betterboto_client

from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet import manifest_utils

logger = logging.getLogger(__name__)


def expand(f, puppet_account_id, single_account, subset=None):
    click.echo("Expanding")
    manifest = manifest_utils.load(f, puppet_account_id)
    org_iam_role_arn = config.get_org_iam_role_arn(puppet_account_id)
    if org_iam_role_arn is None:
        click.echo("No org role set - not expanding")
        new_manifest = manifest
    else:
        click.echo("Expanding using role: {}".format(org_iam_role_arn))
        with betterboto_client.CrossAccountClientContextManager(
            "organizations", org_iam_role_arn, "org-iam-role"
        ) as client:
            new_manifest = manifest_utils.expand_manifest(manifest, client)
    click.echo("Expanded")
    if single_account:
        click.echo(f"Filtering for single account: {single_account}")

        for account in new_manifest.get("accounts", []):
            if str(account.get("account_id")) == str(single_account):
                click.echo(f"Found single account: {single_account}")
                new_manifest["accounts"] = [account]
                break

        click.echo("Filtered")

    new_manifest = manifest_utils.rewrite_cfct(new_manifest)
    new_manifest = manifest_utils.rewrite_depends_on(new_manifest)
    new_manifest = manifest_utils.rewrite_ssm_parameters(new_manifest)
    new_manifest = manifest_utils.rewrite_stacks(new_manifest, puppet_account_id)
    new_manifest = manifest_utils.rewrite_scps(new_manifest, puppet_account_id)

    if subset:
        click.echo(f"Filtering for subset: {subset}")
        new_manifest = manifest_utils.isolate(
            manifest_utils.Manifest(new_manifest), subset
        )

    manifest_accounts_all = [
        {"account_id": a.get("account_id"), "email": a.get("email")}
        for a in new_manifest.get("accounts", [])
    ]
    manifest_accounts_excluding = [
        a for a in manifest_accounts_all if a.get("account_id") != puppet_account_id
    ]

    dumped = json.dumps(new_manifest, default=str)
    sct_manifest_accounts = json.dumps(manifest_accounts_all).replace('"', '\\"')
    dumped = dumped.replace(
        "${AWS::ManifestAccountsAll}", "${SCT::Manifest::Accounts}"
    ).replace("${SCT::Manifest::Accounts}", sct_manifest_accounts)
    sct_manifest_spokes = json.dumps(manifest_accounts_excluding).replace('"', '\\"')
    dumped = dumped.replace(
        "${AWS::ManifestAccountsSpokes}", "${SCT::Manifest::Spokes}"
    ).replace("${SCT::Manifest::Spokes}", sct_manifest_spokes)
    regions = config.get_regions(puppet_account_id)
    sct_config_regions = json.dumps(regions).replace('"', '\\"')
    dumped = dumped.replace("${SCT::Config::Regions}", sct_config_regions)
    new_manifest = json.loads(dumped)
    new_manifest["parameters"]["SCTManifestAccounts"] = dict(
        default=sct_manifest_accounts
    )
    new_manifest["parameters"]["SCTManifestSpokes"] = dict(default=sct_manifest_spokes)
    new_manifest["parameters"]["SCTConfigRegions"] = dict(default=sct_config_regions)
    new_manifest["parameters"]["SCTAccountId"] = dict(default=puppet_account_id)

    if new_manifest.get(constants.LAMBDA_INVOCATIONS) is None:
        new_manifest[constants.LAMBDA_INVOCATIONS] = dict()

    home_region = config.get_home_region(puppet_account_id)
    with betterboto_client.ClientContextManager("ssm") as ssm:
        response = ssm.get_parameter(Name="service-catalog-puppet-version")
        version = response.get("Parameter").get("Value")

    new_manifest["config_cache"] = dict(
        home_region=home_region,
        regions=regions,
        should_collect_cloudformation_events=config.get_should_use_sns(
            puppet_account_id, home_region
        ),
        should_forward_events_to_eventbridge=config.get_should_use_eventbridge(
            puppet_account_id, home_region
        ),
        should_forward_failures_to_opscenter=config.get_should_forward_failures_to_opscenter(
            puppet_account_id, home_region
        ),
        puppet_version=version,
    )

    new_name = f.name.replace(".yaml", "-expanded.yaml")
    logger.info("Writing new manifest: {}".format(new_name))
    with open(new_name, "w") as output:
        output.write(yaml.safe_dump(new_manifest, default_flow_style=False))


def explode(f):
    logger.info("Exploding")
    puppet_account_id = config.get_puppet_account_id()
    original_name = f.name
    expanded_output = f.name.replace(".yaml", "-expanded.yaml")
    expanded_manifest = manifest_utils.load(
        open(expanded_output, "r"), puppet_account_id
    )
    expanded_manifest = manifest_utils.Manifest(expanded_manifest)

    exploded = manifest_utils.explode(expanded_manifest)
    logger.info(f"found {len(exploded)} graphs")
    count = 0
    for mani in exploded:
        with open(original_name.replace(".yaml", f"-exploded-{count}.yaml"), "w") as f:
            f.write(yaml.safe_dump(json.loads(json.dumps(mani))))
        count += 1


def validate(f):
    logger.info("Validating {}".format(f.name))

    manifest = manifest_utils.load(f, config.get_puppet_account_id())

    schema = yamale.make_schema(asset_helpers.resolve_from_site_packages("schema.yaml"))
    data = yamale.make_data(content=yaml.safe_dump(manifest))

    yamale.validate(schema, data, strict=False)

    tags_defined_by_accounts = {}
    for account in manifest.get("accounts"):
        for tag in account.get("tags", []):
            tags_defined_by_accounts[tag] = True

    for collection_type in constants.ALL_SECTION_NAMES:
        collection_to_check = manifest.get(collection_type, {})
        for collection_name, collection_item in collection_to_check.items():
            for deploy_to in collection_item.get("deploy_to", {}).get("tags", []):
                tag_to_check = deploy_to.get("tag")
                if tags_defined_by_accounts.get(tag_to_check) is None:
                    print(
                        f"{collection_type}.{collection_name} uses tag {tag_to_check} in deploy_to that does not exist"
                    )

            for depends_on in collection_item.get("depends_on", []):
                if isinstance(depends_on, str):
                    if manifest.get(constants.LAUNCHES).get(depends_on) is None:
                        print(
                            f"{collection_type}.{collection_name} uses {depends_on} in depends_on that does not exist"
                        )
                else:
                    tt = constants.SECTION_SINGULAR_TO_PLURAL.get(
                        depends_on.get("type", constants.LAUNCH)
                    )
                    dd = depends_on.get("name")
                    if manifest.get(tt).get(dd) is None:
                        print(
                            f"{collection_type}.{collection_name} uses {depends_on} in depends_on that does not exist"
                        )

    click.echo("Finished validating: {}".format(f.name))
    click.echo("Finished validating: OK")


def import_product_set(f, name, portfolio_name):
    url = f"https://raw.githubusercontent.com/awslabs/aws-service-catalog-products/master/{name}/manifest.yaml"
    response = requests.get(url)
    logger.info(f"Getting {url}")
    manifest = yaml.safe_load(f.read())
    if manifest.get("launches") is None:
        manifest["launches"] = {}
    manifest_segment = yaml.safe_load(response.text)
    for launch_name, details in manifest_segment.get("launches").items():
        details["portfolio"] = portfolio_name
        manifest["launches"][launch_name] = details
    with open(f.name, "w") as f:
        f.write(yaml.safe_dump(manifest))


def get_manifest():
    with betterboto_client.ClientContextManager("codecommit") as codecommit:
        content = codecommit.get_file(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            filePath="manifest.yaml",
        ).get("fileContent")
        return yaml.safe_load(content)


def save_manifest(manifest):
    with betterboto_client.ClientContextManager("codecommit") as codecommit:
        parent_commit_id = (
            codecommit.get_branch(
                repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
                branchName="master",
            )
            .get("branch")
            .get("commitId")
        )
        codecommit.put_file(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            branchName="master",
            fileContent=yaml.safe_dump(manifest),
            parentCommitId=parent_commit_id,
            commitMessage="Auto generated commit",
            filePath=f"manifest.yaml",
        )


def add_to_accounts(account_or_ou):
    manifest = get_manifest()
    manifest.get("accounts").append(account_or_ou)
    save_manifest(manifest)


def remove_from_accounts(account_id_or_ou_id_or_ou_path):
    manifest = get_manifest()
    for account in manifest.get("accounts", []):
        if account.get("account_id", "") == account_id_or_ou_id_or_ou_path:
            manifest.get("accounts").remove(account)
            return save_manifest(manifest)
        elif account.get("ou", "") == account_id_or_ou_id_or_ou_path:
            manifest.get("accounts").remove(account)
            return save_manifest(manifest)
    raise Exception(f"Did not remove {account_id_or_ou_id_or_ou_path}")


def add_to_launches(launch_name, launch):
    manifest = get_manifest()
    launches = manifest.get("launches", {})
    launches[launch_name] = launch
    manifest["launches"] = launches
    save_manifest(manifest)


def remove_from_launches(launch_name):
    manifest = get_manifest()
    del manifest.get("launches")[launch_name]
    save_manifest(manifest)
