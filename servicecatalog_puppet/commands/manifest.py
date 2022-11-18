#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import os

import click
import requests
import yamale
import yaml
from betterboto import client as betterboto_client
import networkx as nx
from servicecatalog_puppet import asset_helpers
from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet import print_utils
from servicecatalog_puppet import manifest_utils
from servicecatalog_puppet import serialisation_utils

logger = logging.getLogger(__name__)


def assemble_manifest_from_ssm(target_directory):
    with betterboto_client.ClientContextManager("ssm") as ssm:
        paginator = ssm.get_paginator("get_parameters_by_path")
        manifest = {
            "schema": "puppet-2019-04-01",
            constants.LAUNCHES: dict(),
            constants.STACKS: dict(),
            constants.SPOKE_LOCAL_PORTFOLIOS: dict(),
            constants.ASSERTIONS: {},
            constants.CODE_BUILD_RUNS: {},
            constants.LAMBDA_INVOCATIONS: {},
            constants.APPS: {},
            constants.WORKSPACES: {},
            constants.CFCT: {},
            constants.SERVICE_CONTROL_POLICIES: {},
            constants.SIMULATE_POLICIES: {},
            constants.TAG_POLICIES: {},
        }
        for page in paginator.paginate(
            Path=constants.SERVICE_CATALOG_PUPPET_MANIFEST_SSM_PREFIX, Recursive=True,
        ):
            for parameter in page.get("Parameters", []):
                parts = parameter.get("Name").split("/")
                action_type = parts[3]
                action_name = parts[4]
                manifest[action_type][action_name] = serialisation_utils.load(
                    parameter.get("Value")
                )
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)
        open(f"{target_directory}{os.path.sep}ssm_manifest.yaml", "w").write(
            serialisation_utils.dump(manifest)
        )


def expand(f, puppet_account_id, regions, single_account, subset=None):
    click.echo("Expanding")
    target_directory = os.path.sep.join([os.path.dirname(f.name), "manifests"])
    assemble_manifest_from_ssm(target_directory)
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
            conversions, new_manifest = manifest_utils.expand_manifest(manifest, client)
            new_manifest = manifest_utils.rewrite_organizational_units(
                new_manifest, conversions, client
            )
    click.echo("Expanded")

    new_manifest = manifest_utils.rewrite_deploy_as_share_to_for_spoke_local_portfolios(
        new_manifest
    )
    if single_account:
        click.echo(f"Filtering for single account: {single_account}")

        for account in new_manifest.get("accounts", []):
            if str(account.get("account_id")) == str(single_account):
                click.echo(f"Found single account: {single_account}")
                new_manifest["accounts"] = [account]
                break

        items_to_delete = list()
        for section_name in constants.ALL_SECTION_NAMES:
            deploy_to_name = constants.DEPLOY_TO_NAMES[section_name]
            for item_name, item in new_manifest.get(section_name, {}).items():
                accounts = list()
                for deploy_details in item.get(deploy_to_name, {}).get("accounts", []):
                    if str(deploy_details.get("account_id")) == str(single_account):
                        accounts.append(deploy_details)

                if item.get(deploy_to_name).get("accounts"):
                    if len(accounts) > 0:
                        item[deploy_to_name]["accounts"] = accounts
                    else:
                        if item[deploy_to_name].get("tags") or item[deploy_to_name].get(
                            "ous"
                        ):
                            del item[deploy_to_name]["accounts"]
                        else:
                            items_to_delete.append(f"{section_name}:{item_name}")
        for item_to_delete in items_to_delete:
            section_name, item_name = item_to_delete.split(":")
            del new_manifest[section_name][item_name]

        click.echo("Filtered")

    new_manifest = manifest_utils.rewrite_cfct(new_manifest)
    new_manifest = manifest_utils.rewrite_depends_on(new_manifest)
    new_manifest = manifest_utils.rewrite_ssm_parameters(new_manifest)
    new_manifest = manifest_utils.rewrite_stacks(new_manifest, puppet_account_id)
    new_manifest = manifest_utils.rewrite_scps(new_manifest, puppet_account_id)
    new_manifest = manifest_utils.parse_conditions(new_manifest)

    if subset and subset.get("section"):
        click.echo(f"Filtering for subset: {subset}")
        new_manifest = manifest_utils.isolate(new_manifest, subset)

    manifest_accounts_all = [
        {"account_id": a.get("account_id"), "email": a.get("email")}
        for a in new_manifest.get("accounts", [])
    ]
    manifest_accounts_excluding = [
        a for a in manifest_accounts_all if a.get("account_id") != puppet_account_id
    ]

    # handle all accounts
    sct_manifest_accounts = json.dumps(manifest_accounts_all)
    sct_manifest_spokes = json.dumps(manifest_accounts_excluding)
    sct_config_regions = json.dumps(regions)

    new_manifest["parameters"]["SCTManifestAccounts"] = dict(
        default=sct_manifest_accounts
    )
    new_manifest["parameters"]["SCTManifestSpokes"] = dict(default=sct_manifest_spokes)
    new_manifest["parameters"]["SCTConfigRegions"] = dict(default=sct_config_regions)
    new_manifest["parameters"]["SCTAccountId"] = dict(default=puppet_account_id)

    if new_manifest.get(constants.LAMBDA_INVOCATIONS) is None:
        new_manifest[constants.LAMBDA_INVOCATIONS] = dict()

    new_name = f.name.replace(".yaml", "-expanded.yaml")
    logger.info("Writing new manifest: {}".format(new_name))
    with open(new_name, "w") as output:
        output.write(serialisation_utils.dump(new_manifest))


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
            f.write(serialisation_utils.dump(mani))
        count += 1


def validate(f):
    logger.info("Validating {}".format(f.name))

    manifest = manifest_utils.load(f, config.get_puppet_account_id())

    try:
        Loader = yaml.CSafeLoader
    except AttributeError:  # System does not have libyaml
        Loader = yaml.SafeLoader
    Loader.add_constructor("!Equals", serialisation_utils.Equals.from_yaml)
    Loader.add_constructor("!Not", serialisation_utils.Not.from_yaml)

    schema = yamale.make_schema(asset_helpers.resolve_from_site_packages("schema.yaml"))
    data = yamale.make_data(content=serialisation_utils.dump(manifest))

    yamale.validate(schema, data, strict=False)

    has_default_default_region = (
        manifest.get("defaults", {}).get("accounts", {}).get("default_region", False)
    )
    has_default_regions_enabled = (
        manifest.get("defaults", {}).get("accounts", {}).get("regions_enabled", False)
    )

    graph = nx.DiGraph()

    tags_defined_by_accounts = {}
    for account in manifest.get("accounts"):
        account_entry_is_an_overwrite_or_append = account.get(
            "append", account.get("overwrite", False)
        )
        if (
            not account_entry_is_an_overwrite_or_append
            and account.get("default_region") is None
            and not has_default_default_region
        ):
            raise Exception(
                f"account entry {account.get('account_id', account.get('ou'))} is missing default_region"
            )
        if (
            not account_entry_is_an_overwrite_or_append
            and account.get("regions_enabled") is None
            and not has_default_regions_enabled
        ):
            raise Exception(
                f"account entry {account.get('account_id', account.get('ou'))} is missing regions_enabled"
            )
        for tag in account.get("tags", []):
            tags_defined_by_accounts[tag] = True
        for tag in account.get("append", {}).get("tags", []):
            tags_defined_by_accounts[tag] = True
        for tag in account.get("overwrite", {}).get("tags", []):
            tags_defined_by_accounts[tag] = True

    for collection_type in constants.ALL_SECTION_NAMES:
        collection_to_check = manifest.get(collection_type, {})
        for collection_name, collection_item in collection_to_check.items():
            #
            # Check the tags in deploy_to that are not defined
            #
            for deploy_to in collection_item.get("deploy_to", {}).get("tags", []):
                tag_to_check = deploy_to.get("tag")
                if tags_defined_by_accounts.get(tag_to_check) is None:
                    print_utils.warn(
                        f"{collection_type}.{collection_name} uses tag {tag_to_check} in deploy_to that does not exist",
                    )

            #
            # Check the depends_on where the dependency is not present
            #
            for depends_on in collection_item.get("depends_on", []):
                if isinstance(depends_on, str):
                    if manifest.get(constants.LAUNCHES).get(depends_on) is None:
                        print_utils.warn(
                            f"{collection_type}.{collection_name} uses {depends_on} in depends_on that does not exist",
                        )
                else:
                    tt = constants.SECTION_SINGULAR_TO_PLURAL.get(
                        depends_on.get("type", constants.LAUNCH)
                    )
                    dd = depends_on.get("name")
                    if manifest.get(tt).get(dd) is None:
                        print_utils.warn(
                            f"{collection_type}.{collection_name} uses {depends_on} in depends_on that does not exist",
                        )

            #
            # Check depends_on is present when parameters names match outputs defined elsewhere
            #
            for parameter_name, parameter_details in collection_item.get(
                "parameters", {}
            ).items():
                if parameter_details.get("ssm"):
                    output_name = parameter_details.get("ssm").get("name")
                    for (
                        needle_section_name
                    ) in constants.ALL_SECTION_NAMES_THAT_GENERATE_OUTPUTS:
                        for needle_action_name, needle_action_details in manifest.get(
                            needle_section_name, {}
                        ).items():
                            for needle_output in needle_action_details.get(
                                "outputs", {}
                            ).get("ssm", []):
                                if output_name == needle_output.get("param_name"):
                                    found = False
                                    for d in collection_item.get("depends_on", []):
                                        if isinstance(d, str):
                                            dependency = dict(
                                                type=constants.LAUNCH,
                                                name=d,
                                                affinity=constants.LAUNCH,
                                            )
                                        else:
                                            dependency = d
                                        plural = constants.SECTION_SINGULAR_TO_PLURAL.get(
                                            dependency.get("type", constants.LAUNCH)
                                        )
                                        if (
                                            dependency.get("name") == needle_action_name
                                            and plural == needle_section_name
                                        ):
                                            found = True
                                    if not found:
                                        print_utils.error(
                                            f"{output_name} is used in {collection_type}.{collection_name} from {needle_section_name}.{needle_action_name} but is not in depends_on"
                                        )

            #
            # build graph to check for issues
            #
            uid = f"{collection_type}|{collection_name}"
            data = collection_item
            graph.add_nodes_from(
                [(uid, data),]
            )
            for d in collection_item.get("depends_on", []):
                if isinstance(d, str):
                    dependency = dict(
                        type=constants.LAUNCH, name=d, affinity=constants.LAUNCH
                    )
                else:
                    dependency = d
                plural = constants.SECTION_SINGULAR_TO_PLURAL.get(
                    dependency.get("type", constants.LAUNCH)
                )
                duid = f"{plural}|{dependency.get('name')}"
                graph.add_edge(uid, duid)
    try:
        cycle = nx.find_cycle(graph)
        raise Exception(
            f"found cyclic dependency in your manifest file between: {cycle}"
        )
    except nx.exception.NetworkXNoCycle:
        pass

    print_utils.echo("Finished validating: {}".format(f.name))
    print_utils.echo("Finished validating: OK")


def import_product_set(f, name, portfolio_name):
    url = f"https://raw.githubusercontent.com/awslabs/aws-service-catalog-products/master/{name}/manifest.yaml"
    response = requests.get(url)
    logger.info(f"Getting {url}")
    manifest = serialisation_utils.load(f.read())
    if manifest.get("launches") is None:
        manifest["launches"] = {}
    manifest_segment = serialisation_utils.load(response.text)
    for launch_name, details in manifest_segment.get("launches").items():
        details["portfolio"] = portfolio_name
        manifest["launches"][launch_name] = details
    with open(f.name, "w") as f:
        f.write(serialisation_utils.dump(manifest))


def get_manifest():
    with betterboto_client.ClientContextManager("codecommit") as codecommit:
        content = codecommit.get_file(
            repositoryName=constants.SERVICE_CATALOG_PUPPET_REPO_NAME,
            filePath="manifest.yaml",
        ).get("fileContent")
        return serialisation_utils.load(content)


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
            fileContent=serialisation_utils.dump(manifest),
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
