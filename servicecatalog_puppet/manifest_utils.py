#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import configparser
import json
import logging
import os
import re
from copy import deepcopy

import click
import networkx as nx
from betterboto import client as betterboto_client
from deepmerge import always_merger

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet import serialisation_utils
from servicecatalog_puppet.macros import macros
from servicecatalog_puppet.workflow import tasks

logger = logging.getLogger(__file__)


def get_intrinsic_functions_map(manifest_name, puppet_account_id):
    replacements = dict(AWS=dict(PuppetAccountId=puppet_account_id))
    for intrinsic_function_file in [
        manifest_name.replace("manifest.yaml", "intrinsic-functions.properties"),
        manifest_name.replace(
            "manifest.yaml", f"intrinsic-functions-{puppet_account_id}.properties"
        ),
    ]:
        parser = configparser.SafeConfigParser(
            interpolation=configparser.BasicInterpolation()
        )
        parser.optionxform = str
        if os.path.exists(intrinsic_function_file):
            logger.info(f"reading {intrinsic_function_file}")
            intrinsic_function_file_content = (
                "[Custom]\n" + open(intrinsic_function_file).read()
            )
            parser.read_string(intrinsic_function_file_content)
            for section_name, section_values in parser.items():
                if section_name == "DEFAULT":
                    continue

                if replacements.get(section_name) is None:
                    replacements[section_name] = dict()

                for item_name, item_value in section_values.items():
                    replacements[section_name][item_name] = item_value
    return replacements


def interpolate_intrinsic_functions(contents, intrinsic_functions_map):
    new_contents = contents.replace("", "")
    for section_name, section in intrinsic_functions_map.items():
        for name, value in section.items():
            function_name = "${" + section_name + "::" + name + "}"
            new_contents = new_contents.replace(function_name, value)
    return new_contents


def load(f, puppet_account_id):
    manifest_name = f.name
    manifest = {
        "schema": "puppet-2019-04-01",
        "parameters": {},
        "accounts": [],
        constants.LAUNCHES: {},
        constants.STACKS: {},
        constants.SPOKE_LOCAL_PORTFOLIOS: {},
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
    intrinsic_functions_map = get_intrinsic_functions_map(
        manifest_name, puppet_account_id
    )

    contents = f.read()
    contents = interpolate_intrinsic_functions(contents, intrinsic_functions_map)
    manifest.update(serialisation_utils.load(contents))
    d = os.path.dirname(os.path.abspath(f.name))

    extendable = constants.ALL_SECTION_NAMES + ["parameters"]
    for t in extendable:
        t_path = f"{d}{os.path.sep}{t}"
        if os.path.exists(t_path):
            for f in os.listdir(t_path):
                source = f"{t_path}{os.path.sep}{f}"
                with open(source, "r") as file:
                    contents = file.read()
                    contents = interpolate_intrinsic_functions(
                        contents, intrinsic_functions_map
                    )
                    new = serialisation_utils.load(contents)
                    for n, v in new.items():
                        if manifest[t].get(n):
                            raise Exception(f"{source} declares a duplicate {t}: {n}")
                    manifest[t].update(new)

    if os.path.exists(f"{d}{os.path.sep}manifests"):
        for f in os.listdir(f"{d}{os.path.sep}manifests"):
            with open(f"{d}{os.path.sep}manifests{os.path.sep}{f}", "r") as file:
                contents = file.read()
                contents = interpolate_intrinsic_functions(
                    contents, intrinsic_functions_map
                )
                ext = serialisation_utils.load(contents)
                for t in extendable:
                    manifest[t].update(ext.get(t, {}))

    if os.path.exists(f"{d}{os.path.sep}capabilities"):
        for f in os.listdir(f"{d}{os.path.sep}capabilities"):
            with open(f"{d}{os.path.sep}capabilities{os.path.sep}{f}", "r") as file:
                contents = file.read()
                contents = interpolate_intrinsic_functions(
                    contents, intrinsic_functions_map
                )
                ext = serialisation_utils.load(contents)
                always_merger.merge(manifest, ext)

    for config_file in [
        manifest_name.replace(".yaml", ".properties"),
        manifest_name.replace(".yaml", f"-{puppet_account_id}.properties"),
    ]:
        parser = configparser.ConfigParser(
            interpolation=configparser.BasicInterpolation()
        )
        parser.optionxform = str

        if os.path.exists(config_file):
            logger.info(f"reading {config_file}")
            parser.read(config_file)

            for section_name, section_values in parser.items():
                if section_name == "DEFAULT":
                    continue
                for item_name, item_value in section_values.items():
                    name, property_name = item_name.split(".")
                    if property_name not in ["version", "condition", "status"]:
                        raise Exception(
                            "You can only specify a version in the properties file"
                        )
                    if manifest.get(section_name, {}).get(name):
                        manifest[section_name][name][property_name] = item_value
                    else:
                        logger.warning(
                            f"Could not find manifest[{section_name}][{name}]"
                        )

    for section in constants.ALL_SPOKE_EXECUTABLE_SECTION_NAMES:
        for name, details in manifest.get(section, {}).items():
            if details.get("execution") is None:
                details["execution"] = constants.EXECUTION_MODE_DEFAULT
    return manifest


def expand_manifest(manifest, client):
    new_manifest = deepcopy(manifest)
    temp_accounts = []
    conversions = dict()

    logger.info("Starting the expand")

    for account in manifest.get("accounts"):
        if account.get("account_id"):
            account_id = account.get("account_id")
            logger.info("Found an account: {}".format(account_id))
            expanded_account = expand_account(account, client, account_id, manifest)
            if expanded_account is None:
                raise Exception(
                    f"You have listed account: {account_id} which is not ACTIVE"
                )
            temp_accounts.append(expanded_account)
        elif account.get("ou"):
            ou = account.get("ou")
            logger.info("Found an ou: {}".format(ou))
            if ou.startswith("/"):
                ou = client.convert_path_to_ou(account.get("ou"))
                conversions[account.get("ou")] = ou
                account["ou_name"] = account["ou"]
                account["ou"] = ou
            temp_accounts += expand_ou(account, client, manifest)

    for parameter_name, parameter_details in new_manifest.get("parameters", {}).items():
        if parameter_details.get("macro"):
            macro_to_run = macros.get(parameter_details.get("macro").get("method"))
            result = macro_to_run(client, parameter_details.get("macro").get("args"))
            parameter_details["default"] = result
            del parameter_details["macro"]

    accounts_by_id = {}
    for account in temp_accounts:
        for parameter_name, parameter_details in account.get("parameters", {}).items():
            if parameter_details.get("macro"):
                macro_to_run = macros.get(parameter_details.get("macro").get("method"))
                result = macro_to_run(
                    client, parameter_details.get("macro").get("args")
                )
                parameter_details["default"] = result
                del parameter_details["macro"]

        account_id = account.get("account_id")
        if account.get("append") or account.get("overwrite"):
            if (
                account.get("default_region")
                or account.get("regions_enabled")
                or account.get("tags")
            ):
                raise Exception(
                    f"{account_id}: If using append or overwrite you cannot set default_region, regions_enabled or tags"
                )

        if accounts_by_id.get(account_id) is None:
            accounts_by_id[account_id] = account
        else:
            logger.debug("Found an already seen account")
            if not (account.get("append") or account.get("overwrite")):
                raise Exception(
                    f"Account {account_id} was seen more than once without an append or overwrite"
                )
            accounts_by_id[account_id].update(account)

    for stored_account_id, stored_account in accounts_by_id.items():
        # Get tags from orgs if we should
        organizations_account_tags = stored_account.get(
            "organizations_account_tags", "ignored"
        )
        if organizations_account_tags != "ignored":
            tags = list()
            paginator = client.get_paginator("list_tags_for_resource")
            for page in paginator.paginate(ResourceId=stored_account_id,):
                tags.extend(page.get("Tags", []))
            tags = [f"{t['Key']}:{t['Value']}" for t in tags]

            if organizations_account_tags == "append":
                stored_account["tags"] = stored_account.get("tags", []) + tags
            elif organizations_account_tags == "honour":
                stored_account["tags"] = tags

        # append or overwrite if we should
        if stored_account.get("append"):
            append = stored_account.get("append")
            for tag in append.get("tags", []):
                stored_account["tags"] = stored_account.get("tags", []) + [tag]
            for region_enabled in append.get("regions_enabled", []):
                stored_account["regions_enabled"] = stored_account.get(
                    "regions_enabled", []
                ) + [region_enabled]
            del stored_account["append"]

        elif stored_account.get("overwrite"):
            overwrite = stored_account.get("overwrite")
            if overwrite.get("tags"):
                stored_account["tags"] = overwrite.get("tags")
            if overwrite.get("regions_enabled"):
                stored_account["regions_enabled"] = overwrite.get("regions_enabled")
            if overwrite.get("default_region"):
                stored_account["default_region"] = overwrite.get("default_region")
            del stored_account["overwrite"]

    new_manifest["accounts"] = list(accounts_by_id.values())

    for section in [constants.LAUNCHES, constants.STACKS]:
        for name, details in new_manifest.get(section, {}).items():
            for parameter_name, parameter_details in details.get(
                "parameters", {}
            ).items():
                if parameter_details.get("macro"):
                    macro_to_run = macros.get(
                        parameter_details.get("macro").get("method")
                    )
                    result = macro_to_run(
                        client, parameter_details.get("macro").get("args")
                    )
                    parameter_details["default"] = result
                    del parameter_details["macro"]

    return conversions, new_manifest


def rewrite_deploy_as_share_to_for_spoke_local_portfolios(manifest):
    for item_name, item in manifest.get(constants.SPOKE_LOCAL_PORTFOLIOS, {}).items():
        if item.get("deploy_to"):
            item["share_with"] = item["deploy_to"]
            del item["deploy_to"]
    return manifest


def rewrite_cfct(manifest):
    manifest_accounts = dict()
    for account in manifest.get("accounts", []):
        if account.get("account_id"):
            manifest_accounts[account.get("name")] = account.get("account_id")

    prev = None
    for instance in manifest.get(constants.CFCT, []):
        if str(instance.get("version")) != "2021-03-15":
            raise Exception(
                f"not supported version of cfct manifest {instance.get('version')}"
            )
        default_region = instance.get("region")
        for resource in instance.get("resources", []):
            resource_file = resource.get("resource_file").lower()
            if resource_file.startswith("s3://"):
                m = re.match(r"s3://(.*)/(.*)", resource_file)
                bucket = m.group(1)
                key = m.group(2)
            elif resource_file.startswith("https://"):
                m = re.match(r"https://([a-z0-9-]+)(.*)/(.*)", resource_file)
                bucket = m.group(1)
                key = m.group(3)
            else:
                raise Exception(
                    f"All resource files should begin with s3:// of https://: {resource_file}"
                )

            name = resource.get("name")
            deploy_method = resource.get("deploy_method")

            if deploy_method == "stack_set":
                parameters = dict()
                depends_on = list()
                ssm = list()
                outputs = dict(ssm=ssm)
                deploy_to_accounts = list()
                deploy_to_tags = list()
                deploy_to = dict(tags=deploy_to_tags, accounts=deploy_to_accounts)

                if resource.get("parameter_file"):
                    parameter_file = resource.get("parameter_file")
                    if parameter_file.startswith("s3://"):
                        m = re.match(r"s3://(.*)/(.*)", parameter_file)
                        bucket = m.group(1)
                        key = m.group(2)
                    elif parameter_file.startswith("https://"):
                        m = re.match(r"https://([a-z0-9-]+)(.*)/(.*)", parameter_file)
                        bucket = m.group(1)
                        key = m.group(3)
                    else:
                        raise Exception(
                            f"All parameter_files should begin with s3:// of https://: {parameter_file}"
                        )
                    with betterboto_client.ClientContextManager("s3") as s3:
                        p = s3.get_object(Bucket=bucket, Key=key).read()
                        resource["parameters"] = serialisation_utils.json_loads(p)

                for p in resource.get("parameters", []):
                    parameter_key = p.get("parameter_key")
                    parameter_value = p.get("parameter_value")
                    m = re.match(r"\$\[alfred_ssm_(.*)\]", parameter_value)
                    if m:
                        parameters[parameter_key] = dict(
                            ssm=dict(name=m.group(1), region=default_region,)
                        )
                    else:
                        parameters[parameter_key] = dict(default=parameter_value)

                if prev is not None:
                    depends_on.append(
                        dict(name=prev, type=constants.STACK, affinity=constants.STACK,)
                    )

                for output in resource.get("export_outputs", []):
                    output_value = re.match(
                        r"\$\[output_(.*)\]", output.get("value")
                    ).group(1)
                    ssm.append(
                        dict(param_name=output.get("name"), stack_output=output_value)
                    )

                regions = resource.get("regions", [default_region])
                for account in resource.get("deployment_targets", {}).get(
                    "accounts", []
                ):
                    if re.match(r"[0-9]{12}", str(account)):
                        deploy_to_accounts.append(
                            dict(account_id=account, regions=regions)
                        )
                    else:
                        if manifest_accounts.get(account) is None:
                            raise Exception(
                                f"You are using CFCT resource: {name} to deploy to account: {account} which is not defined in your accounts section"
                            )
                        deploy_to_accounts.append(
                            dict(
                                account_id=manifest_accounts.get(account),
                                regions=regions,
                            )
                        )

                for organizational_unit in resource.get("deployment_targets", {}).get(
                    "organizational_units", []
                ):
                    deploy_to_tags.append(
                        dict(
                            tag=f"autogenerated:{organizational_unit}", regions=regions
                        )
                    )

                stack = dict(
                    name=name,
                    stack_set_name=name,
                    bucket=bucket,
                    key=key,
                    execution=constants.EXECUTION_MODE_HUB,
                    capabilities=["CAPABILITY_NAMED_IAM"],
                    parameters=parameters,
                    depends_on=depends_on,
                    outputs=outputs,
                    deploy_to=deploy_to,
                )

                if manifest.get(constants.STACKS) is None:
                    manifest[constants.STACKS] = dict()
                if manifest[constants.STACKS].get(name) is not None:
                    raise Exception(
                        f"You have a stack and a cfct resource with the same name: {name}"
                    )
                manifest[constants.STACKS][name] = stack

                prev = name

            elif deploy_method == "scp":
                with betterboto_client.ClientContextManager("s3") as s3:
                    p = s3.get_object(Bucket=bucket, Key=key).read()
                    content = serialisation_utils.json_loads(p)

                depends_on = list()
                deploy_to_accounts = list()
                deploy_to_ous = list()
                deploy_to = dict(accounts=deploy_to_accounts, ous=deploy_to_ous)

                if prev is not None:
                    depends_on.append(
                        dict(
                            name=prev,
                            type=constants.SERVICE_CONTROL_POLICY,
                            affinity=constants.SERVICE_CONTROL_POLICY,
                        )
                    )

                regions = "home_region"
                for account in resource.get("deployment_targets", {}).get(
                    "accounts", []
                ):
                    if re.match(r"[0-9]{12}", str(account)):
                        deploy_to_accounts.append(
                            dict(account_id=account, regions=regions)
                        )
                    else:
                        if manifest_accounts.get(account) is None:
                            raise Exception(
                                f"You are using CFCT resource: {name} to deploy to account: {account} which is not defined in your accounts section"
                            )
                        deploy_to_accounts.append(
                            dict(
                                account_id=manifest_accounts.get(account),
                                regions=regions,
                            )
                        )

                for organizational_unit in resource.get("deployment_targets", {}).get(
                    "organizational_units", []
                ):
                    deploy_to_ous.append(dict(ou=organizational_unit, regions=regions))

                scp = dict(
                    description=resource.get("description", "auto generated from CfCT"),
                    content=dict(default=content),
                    depends_on=depends_on,
                    apply_to=deploy_to,
                )

                if manifest.get(constants.SERVICE_CONTROL_POLICIES) is None:
                    manifest[constants.SERVICE_CONTROL_POLICIES] = dict()
                if manifest[constants.SERVICE_CONTROL_POLICIES].get(name) is not None:
                    raise Exception(
                        f"You have an SCP and a cfct resource with the same name: {name}"
                    )
                manifest[constants.SERVICE_CONTROL_POLICIES][name] = scp

                prev = name

            else:
                raise Exception(f"Unknown deploy_method of {deploy_method}")

    return manifest


def rewrite_depends_on(manifest):
    for (
        section_item_name,
        section_name,
    ) in constants.ALL_SECTION_NAME_SINGULAR_AND_PLURAL_LIST:
        for item, details in manifest.get(section_name, {}).items():
            for i in range(len(details.get("depends_on", []))):
                if isinstance(details["depends_on"][i], str):
                    manifest[section_name][item]["depends_on"][i] = dict(
                        name=details["depends_on"][i], type="launch",
                    )
                if isinstance(details["depends_on"][i], dict):
                    if details["depends_on"][i].get(constants.AFFINITY) is None:
                        details["depends_on"][i][constants.AFFINITY] = details[
                            "depends_on"
                        ][i]["type"]
    return manifest


def rewrite_ssm_parameters(manifest):
    """
    when an item in a section of the manifest uses an ssm parameter this will add a depends on to the ssm parameter
    where it finds the parameter being set up by the output of a dependency.
    :param manifest:
    :return:
    """
    for (
        section_item_name,
        section_name,
    ) in constants.SECTION_NAME_SINGULAR_AND_PLURAL_LIST_THAT_SUPPORTS_PARAMETERS:
        for item, details in manifest.get(section_name, {}).items():
            for parameter_name, parameter_details in details.get(
                "parameters", {}
            ).items():
                if parameter_details.get("cloudformation_stack_output"):
                    existing_parameter = parameter_details.get(
                        "cloudformation_stack_output"
                    )
                    stack_name = existing_parameter.get("stack_name")
                    output_key = existing_parameter.get("output_key")
                    new_parameter = dict(
                        account_id=existing_parameter.get(
                            "account_id", "${AWS::AccountId}"
                        ),
                        region=existing_parameter.get("region", "${AWS::Region}"),
                        client="cloudformation",
                        call="describe_stacks",
                        use_paginator=True,
                        arguments=dict(StackName=stack_name),
                        filter=f"Stacks[?StackStatus==`CREATE_COMPLETE` || StackStatus==`UPDATE_COMPLETE`|| StackStatus==`UPDATE_ROLLBACK_COMPLETE`].Outputs[] | [?OutputKey==`{output_key}`].OutputValue | [0]",
                    )
                    parameter_details["boto3"] = new_parameter

                if parameter_details.get("servicecatalog_provisioned_product_output"):
                    existing_parameter = parameter_details.get(
                        "servicecatalog_provisioned_product_output"
                    )
                    provisioned_product_name = existing_parameter.get(
                        "provisioned_product_name"
                    )
                    output_key = existing_parameter.get("output_key")
                    new_parameter = dict(
                        account_id=existing_parameter.get(
                            "account_id", "${AWS::AccountId}"
                        ),
                        region=existing_parameter.get("region", "${AWS::Region}"),
                        client="servicecatalog",
                        call="get_provisioned_product_outputs",
                        use_paginator=False,
                        arguments=dict(ProvisionedProductName=provisioned_product_name),
                        filter=f"Outputs[?OutputKey==`{output_key}`].OutputValue | [0]",
                    )
                    parameter_details["boto3"] = new_parameter
    return manifest


def rewrite_stacks(manifest, puppet_account_id):
    for category, section in [
        (constants.STACK, constants.STACKS),
        (constants.APP, constants.APPS),
        (constants.WORKSPACE, constants.WORKSPACES),
    ]:
        for item, details in manifest.get(section, {}).items():
            if not details.get("key"):
                if category == constants.STACK:
                    details[
                        "key"
                    ] = f"{category}/{details['name']}/{details['version']}/{category}.template-${{AWS::Region}}.yaml"
                else:
                    details[
                        "key"
                    ] = f"{category}/{details['name']}/{details['version']}/{category}.zip"
                del details["name"]
                del details["version"]
                if category == constants.STACK:
                    if (
                        details.get(constants.MANIFEST_SHOULD_USE_STACKS_SERVICE_ROLE)
                        is None
                    ):
                        details[
                            constants.MANIFEST_SHOULD_USE_STACKS_SERVICE_ROLE
                        ] = config.get_should_use_stacks_service_role(puppet_account_id)
    return manifest


def rewrite_scps(manifest, puppet_account_id):
    for item, details in manifest.get(constants.SERVICE_CONTROL_POLICIES, {}).items():
        for attribute in ["tags", "accounts", "ous"]:
            apply_to = details.get("apply_to")
            for d in apply_to.get(attribute, []):
                d["regions"] = "home_region"
    for item, details in manifest.get(constants.TAG_POLICIES, {}).items():
        for attribute in ["tags", "accounts", "ous"]:
            apply_to = details.get("apply_to")
            for d in apply_to.get(attribute, []):
                d["regions"] = "home_region"
    return manifest


def expand_path(account, client, manifest):
    ou = client.convert_path_to_ou(account.get("ou"))
    account["ou_name"] = account["ou"]
    account["ou"] = ou
    return expand_ou(account, client, manifest)


def expand_account(account, client, account_id, manifest):
    response = client.describe_account(AccountId=account_id)

    new_account = deepcopy(manifest.get("defaults", {}).get("accounts", {}))
    new_account.update(deepcopy(account))

    ou_from_parent = None
    if "ou" in new_account:
        ou_from_parent = new_account["ou"]
        del new_account["ou"]

    account_details = response.get("Account")
    if account_details.get("Status") == "ACTIVE":
        if account_details.get("Name") is not None:
            new_account["name"] = account_details.get("Name")
        new_account["email"] = account_details.get("Email")
        if ou_from_parent is not None:
            new_account["expanded_from"] = ou_from_parent
            new_account["account_id"] = account_id
        new_account["organization"] = (
            account_details.get("Arn").split(":")[5].split("/")[1]
        )
        return new_account
    else:
        logger.info(
            f"Skipping account as it is not ACTIVE: {json.dumps(account_details, default=str)}"
        )
    return None


def expand_ou(original_account, client, manifest):
    expanded = []
    exclusions = original_account.get("exclude", {}).get("accounts", [])
    ou_exclusions = original_account.get("exclude", {}).get("ous", [])
    for ou_exclusion in ou_exclusions:
        if ou_exclusion.startswith("/"):
            ou_id = client.convert_path_to_ou(ou_exclusion)
        else:
            ou_id = ou_exclusion
        children = client.list_children_nested(ParentId=ou_id, ChildType="ACCOUNT")
        for child in children:
            logger.info(
                f"Adding {child.get('Id')} to the exclusion list as it was in the ou {ou_exclusion}"
            )
            exclusions.append(child.get("Id"))

    response = client.list_children_nested(
        ParentId=original_account.get("ou"), ChildType="ACCOUNT"
    )
    for result in response:
        new_account_id = result.get("Id")
        if new_account_id in exclusions:
            logger.info(f"Skipping {new_account_id} as it is in the exclusion list")
            continue
        new_account = expand_account(original_account, client, new_account_id, manifest)
        if new_account:
            expanded.append(new_account)
    return expanded


def get_configuration_overrides(manifest, launch_details):
    configuration = dict()
    if manifest.get("configuration"):
        if manifest.get("configuration").get("retry_count"):
            configuration["retry_count"] = manifest.get("configuration").get(
                "retry_count"
            )
    if launch_details.get("configuration"):
        if launch_details.get("configuration").get("retry_count"):
            configuration["retry_count"] = launch_details.get("configuration").get(
                "retry_count"
            )
        if launch_details.get("configuration").get("requested_priority"):
            configuration["requested_priority"] = int(
                launch_details.get("configuration").get("requested_priority")
            )
    return configuration


def get_from_dict(d, path):
    parts = path.split("/")
    if len(parts) == 1:
        result = d.get(parts[0])
    elif len(parts) == 2:
        result = d.get(parts[0], {}).get(parts[1])
    elif len(parts) == 3:
        result = d.get(parts[0], {}).get(parts[1], {}).get(parts[2])
    if result is None:
        raise KeyError
    return result


class Manifest(dict):
    def has_cache(self):
        return self.get("id_cache") is not None

    def get_launches_items(self):
        return self.get(constants.LAUNCHES, {}).items()

    def get_launch(self, name):
        return self.get(constants.LAUNCHES).get(name)

    def get_workspace(self, name):
        return self.get(constants.WORKSPACES).get(name)

    def get_app(self, name):
        return self.get(constants.APPS).get(name)

    def get_tasks_for(
        self,
        puppet_account_id,
        section_name,
        item_name,
        home_region_configured,
        regions_configured,
        single_account="None",
    ):
        accounts = self.get(constants.ACCOUNTS)
        section = self.get(section_name)
        provisioning_tasks = list()
        item = section[item_name]
        sharing_mode_default = config.get_global_sharing_mode_default()
        share_tag_options_default = config.get_global_share_tag_options_default()
        share_principals_default = config.get_global_share_principals_default()

        deploy_to = {
            "launches": "deploy_to",
            "stacks": "deploy_to",
            "apps": "deploy_to",
            "workspaces": "deploy_to",
            "spoke-local-portfolios": "share_with",
            "lambda-invocations": "invoke_for",
            "code-build-runs": "run_for",
            "assertions": "assert_for",
            "service-control-policies": "apply_to",
            "tag-policies": "apply_to",
            "simulate-policies": "simulate_for",
            constants.ORGANIZATIONAL_UNITS: "create_in",
        }.get(section_name)

        if (
            section_name == constants.SPOKE_LOCAL_PORTFOLIOS
            and item.get(deploy_to) is None
        ):
            deploy_to = "deploy_to"

        common_parameters = {
            "launches": dict(
                launch_name=item_name,
                # launch_parameters=item.get("parameters", {}),
                # manifest_parameters=self.get("parameters", {}),
                ssm_param_outputs=item.get("outputs", {}).get("ssm", []),
                share_tag_options=item.get(
                    "share_tag_options", share_tag_options_default
                ),
                share_principals=item.get("share_principals", share_principals_default),
                portfolio=item.get("portfolio"),
                product=item.get("product"),
                version=item.get("version"),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
                tags=item.get("tags", []),
            ),
            "stacks": dict(
                stack_name=item_name,
                launch_name=item.get("launch_name", ""),
                stack_set_name=item.get("stack_set_name", ""),
                # launch_parameters=item.get("parameters", {}),
                capabilities=item.get("capabilities", []),
                # manifest_parameters=self.get("parameters", {}),
                ssm_param_outputs=item.get("outputs", {}).get("ssm", []),
                bucket=f"sc-puppet-stacks-repository-{puppet_account_id}",
                key=item.get("key"),
                version_id=item.get("version_id", ""),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
                use_service_role=item.get(
                    constants.MANIFEST_SHOULD_USE_STACKS_SERVICE_ROLE,
                    constants.CONFIG_SHOULD_USE_STACKS_SERVICE_ROLE_DEFAULT,
                ),
                tags=item.get("tags", []),
            ),
            "apps": dict(
                app_name=item_name,
                # launch_parameters=item.get("parameters", {}),
                # manifest_parameters=self.get("parameters", {}),
                ssm_param_outputs=item.get("outputs", {}).get("ssm", []),
                bucket=f"sc-puppet-stacks-repository-{puppet_account_id}",
                key=item.get("key"),
                version_id=item.get("version_id", ""),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
            ),
            "workspaces": dict(
                workspace_name=item_name,
                # launch_parameters=item.get("parameters", {}),
                # manifest_parameters=self.get("parameters", {}),
                ssm_param_outputs=item.get("outputs", {}).get("ssm", []),
                bucket=f"sc-puppet-stacks-repository-{puppet_account_id}",
                key=item.get("key"),
                version_id=item.get("version_id", ""),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
            ),
            "spoke-local-portfolios": dict(
                spoke_local_portfolio_name=item_name,
                product_generation_method=item.get(
                    "product_generation_method",
                    constants.PRODUCT_GENERATION_METHOD_DEFAULT,
                ),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
                sharing_mode=item.get("sharing_mode", sharing_mode_default),
                share_tag_options=item.get(
                    "share_tag_options", share_tag_options_default
                ),
                share_principals=item.get("share_principals", share_principals_default),
                associations=item.get("associations", list()),
                launch_constraints=item.get("constraints", {}).get("launch", []),
                resource_update_constraints=item.get("constraints", {}).get(
                    "resource_update", []
                ),
                portfolio=item.get("portfolio"),
            ),
            "lambda-invocations": dict(
                lambda_invocation_name=item_name,
                function_name=item.get("function_name"),
                qualifier=item.get("qualifier", "$LATEST"),
                invocation_type=item.get("invocation_type"),
                # launch_parameters=item.get("parameters", {}),
                # manifest_parameters=self.get("parameters", {}),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
            ),
            "code-build-runs": dict(
                code_build_run_name=item_name,
                # launch_parameters=item.get("parameters", {}),
                # manifest_parameters=self.get("parameters", {}),
                project_name=item.get("project_name"),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
            ),
            "assertions": dict(
                assertion_name=item_name,
                expected=item.get("expected"),
                actual=item.get("actual"),
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
            ),
            "service-control-policies": dict(
                service_control_policy_name=item_name,
                description=item.get("description"),
                content=tasks.unwrap(item.get("content")),
            ),
            "tag-policies": dict(
                tag_policy_name=item_name,
                description=item.get("description"),
                content=tasks.unwrap(item.get("content")),
            ),
            constants.SIMULATE_POLICIES: dict(
                execution=item.get("execution", constants.EXECUTION_MODE_DEFAULT),
                simulate_policy_name=item_name,
                simulation_type=item.get("simulation_type"),
                policy_source_arn=item.get("policy_source_arn", ""),
                policy_input_list=item.get("policy_input_list", []),
                permissions_boundary_policy_input_list=item.get(
                    "permissions_boundary_policy_input_list", []
                ),
                action_names=item.get("action_names"),
                expected_decision=item.get("expected_decision"),
                resource_arns=item.get("resource_arns", []),
                resource_policy=item.get("resource_policy", ""),
                resource_owner=item.get("resource_owner", ""),
                caller_arn=item.get("caller_arn", ""),
                context_entries=item.get("context_entries", []),
                resource_handling_option=item.get("resource_handling_option", ""),
            ),
            constants.ORGANIZATIONAL_UNITS: dict(
                organizational_unit_name=item_name,
                path=item.get("path"),
                parent_ou_id=item.get("parent_ou_id"),
                name=item.get("name"),
                tags=item.get("tags"),
            ),
        }.get(section_name)

        common_parameters.update(
            dict(
                puppet_account_id=puppet_account_id,
                status=item.get("status"),
                requested_priority=item.get("requested_priority", 0),
                dependencies=item.get("depends_on", []),
            )
        )

        # handle deploy_to tags
        tags = item.get(deploy_to).get("tags", [])
        for tag in tags:
            tag_name = tag.get("tag")
            regions = tag.get("regions")
            for account in accounts:
                account_id = str(account.get("account_id"))
                if single_account != "None" and single_account != account_id:
                    continue
                additional_parameters = {
                    "launches": dict(
                        account_id=account_id, ou=account.get("expanded_from", ""),
                    ),
                    "apps": dict(account_id=account_id,),
                    "workspaces": dict(account_id=account_id,),
                    "stacks": dict(account_id=account_id,),
                    "spoke-local-portfolios": dict(
                        account_id=account_id,
                        organization=account.get("organization", ""),
                        ou=account.get("expanded_from", ""),
                    ),
                    "assertions": dict(account_id=account_id,),
                    "lambda-invocations": dict(account_id=account_id,),
                    "code-build-runs": dict(account_id=account_id,),
                    "service-control-policies": dict(
                        account_id=account_id, ou_name="",
                    ),
                    "tag-policies": dict(account_id=account_id, ou_name="",),
                    constants.SIMULATE_POLICIES: dict(account_id=account_id,),
                }.get(section_name)
                if tag_name in account.get("tags"):
                    if isinstance(regions, str):
                        if regions in [
                            "enabled",
                            "regions_enabled",
                            "enabled_regions",
                        ]:
                            for region_enabled in account.get("regions_enabled"):
                                provisioning_tasks.append(
                                    dict(
                                        **common_parameters,
                                        **additional_parameters,
                                        region=region_enabled,
                                    )
                                )
                        elif regions == "default_region":
                            provisioning_tasks.append(
                                dict(
                                    **common_parameters,
                                    **additional_parameters,
                                    region=account.get("default_region"),
                                )
                            )
                        elif regions == "home_region":
                            provisioning_tasks.append(
                                dict(
                                    **common_parameters,
                                    **additional_parameters,
                                    region=home_region_configured,
                                )
                            )
                        elif regions == "all":
                            all_regions = regions_configured
                            for region_enabled in all_regions:
                                provisioning_tasks.append(
                                    dict(
                                        **common_parameters,
                                        **additional_parameters,
                                        region=region_enabled,
                                    )
                                )

                        else:
                            raise Exception(
                                f"Unsupported regions {regions} setting for {section_name}: {item_name}"
                            )
                    elif isinstance(regions, list):
                        for region_ in regions:
                            provisioning_tasks.append(
                                dict(
                                    **common_parameters,
                                    **additional_parameters,
                                    region=region_,
                                )
                            )
                    elif isinstance(regions, tuple):
                        for region_ in regions:
                            provisioning_tasks.append(
                                dict(
                                    **common_parameters,
                                    **additional_parameters,
                                    region=region_,
                                )
                            )

                    else:
                        raise Exception(
                            f"Unsupported regions {regions} setting for {section_name}: {item_name}"
                        )

        # handle deploy_to accounts
        for account_to_deploy_to in item.get(deploy_to).get("accounts", []):
            account_id_of_account_to_deploy_to = account_to_deploy_to.get("account_id")
            regions = account_to_deploy_to.get("regions")

            account = self.get_account(account_id_of_account_to_deploy_to)
            account_id = account_id_of_account_to_deploy_to
            if single_account != "None" and single_account != account_id:
                continue
            additional_parameters = {
                "launches": dict(account_id=account_id,),
                "stacks": dict(account_id=account_id,),
                "spoke-local-portfolios": dict(account_id=account_id,),
                "assertions": dict(account_id=account_id,),
                "lambda-invocations": dict(account_id=account_id,),
                "code-build-runs": dict(account_id=account_id,),
                "service-control-policies": dict(account_id=account_id, ou_name="",),
                "tag-policies": dict(account_id=account_id, ou_name="",),
                constants.SIMULATE_POLICIES: dict(account_id=account_id,),
                constants.ORGANIZATIONAL_UNITS: dict(account_id=account_id,),
            }.get(section_name)

            if isinstance(regions, str):
                if regions in [
                    "enabled",
                    "regions_enabled",
                    "enabled_regions",
                ]:
                    for region_enabled in account.get("regions_enabled"):
                        provisioning_tasks.append(
                            dict(
                                **common_parameters,
                                **additional_parameters,
                                region=region_enabled,
                            )
                        )
                elif regions == "default_region":
                    provisioning_tasks.append(
                        dict(
                            **common_parameters,
                            **additional_parameters,
                            region=account.get("default_region"),
                        )
                    )
                elif regions == "home_region":
                    provisioning_tasks.append(
                        dict(
                            **common_parameters,
                            **additional_parameters,
                            region=home_region_configured,
                        )
                    )
                elif regions == "all":
                    all_regions = regions_configured
                    for region_enabled in all_regions:
                        provisioning_tasks.append(
                            dict(
                                **common_parameters,
                                **additional_parameters,
                                region=region_enabled,
                            )
                        )

                else:
                    raise Exception(
                        f"Unsupported regions {regions} setting for {section_name}: {item_name}"
                    )
            elif isinstance(regions, list):
                for region_ in regions:
                    provisioning_tasks.append(
                        dict(
                            **common_parameters,
                            **additional_parameters,
                            region=region_,
                        )
                    )
            elif isinstance(regions, tuple):
                for region_ in regions:
                    provisioning_tasks.append(
                        dict(
                            **common_parameters,
                            **additional_parameters,
                            region=region_,
                        )
                    )

            else:
                raise Exception(
                    f"Unsupported regions {regions} setting for {section_name}: {item_name}"
                )

        # handle deploy_to ous
        for ou_to_deploy_to in item.get(deploy_to).get("ous", []):
            ou_name = ou_to_deploy_to.get("ou")
            regions = ou_to_deploy_to.get("regions")

            if single_account != "None":
                continue

            additional_parameters = {
                "service-control-policies": dict(account_id="", ou_name=ou_name,),
                "tag-policies": dict(account_id="", ou_name=ou_name,),
            }.get(section_name)

            if isinstance(regions, str) and regions == "home_region":
                provisioning_tasks.append(
                    dict(
                        **common_parameters,
                        **additional_parameters,
                        region=home_region_configured,
                    )
                )
            else:
                raise Exception(
                    f"Unsupported regions {regions} setting for {section_name}: {item_name}"
                )

        return provisioning_tasks

    def get_account_ids_used_for_section_item(
        self, puppet_account_id, section_name, item_name
    ):
        return list(
            set(
                task.get("account_id")
                for task in self.get_tasks_for(
                    puppet_account_id, section_name, item_name
                )
            )
        )

    def get_account_ids_and_regions_used_for_section_item(
        self, puppet_account_id, section_name, item_name
    ):
        result = dict()
        for task in self.get_tasks_for(puppet_account_id, section_name, item_name):
            if result.get(task.get("account_id")) is None:
                result[task.get("account_id")] = list()
            result[task.get("account_id")].append(task.get("region"))
        for account_id in result.keys():
            result[account_id] = list(set(result[account_id]))
        return result

    def get_mapping(self, mapping, account_id, region):
        manifest_mappings = self.get("mappings")
        new_mapping = []
        for item in mapping:
            if item == "AWS::AccountId":
                new_mapping.append(account_id)
            elif item == "AWS::Region":
                new_mapping.append(region)
            else:
                new_mapping.append(item)
        path_to_find = "/".join(new_mapping)
        result = None
        try:
            result = get_from_dict(manifest_mappings, path_to_find)
        except KeyError:
            logger.debug(f"Could not find: {path_to_find}")
            while len(new_mapping) > 0:
                new_mapping[-1] = "default"
                path_to_find = "/".join(new_mapping)
                try:
                    logger.info(f"now looking for {path_to_find}")
                    result = get_from_dict(manifest_mappings, path_to_find)
                    break
                except KeyError:
                    logger.info(f"Could not find {path_to_find}")
                    new_mapping.pop()

        if result is None:
            raise Exception(f"Could not find: {'' + '/'.join(mapping)}")
        return result

    def get_account(self, account_id):
        for account in self.get("accounts"):
            if account.get("account_id") == str(account_id):
                return account
        raise Exception(f"Could not find account: {account_id}")

    def get_parameters_for_account(self, account_id):
        for account in self.get("accounts"):
            if account.get("account_id") == str(account_id):
                return account.get("parameters", {})
        return dict()

    def get_sharing_policies_by_region(self):
        sharing_policies_by_region = {}
        for account in self.get("accounts"):
            account_regions = list()
            if account.get("default_region") is None:
                raise Exception(
                    f"Account {account.get('account_id')} has no default_region"
                )
            account_regions.append(account.get("default_region"))

            enabled_regions = (
                account.get("enabled", [])
                + account.get("regions_enabled", [])
                + account.get("enabled_regions", [])
            )
            if len(enabled_regions) == 0:
                raise Exception(
                    f"Account {account.get('account_id')} has no enabled|regions_enabled|enabled_regions"
                )
            account_regions += enabled_regions

            for r in account_regions:
                if sharing_policies_by_region.get(r) is None:
                    sharing_policies_by_region[r] = dict(accounts=[], organizations=[])
                if account.get("organization", "") != "":
                    organization = account.get("organization")
                    if (
                        organization
                        not in sharing_policies_by_region[r]["organizations"]
                    ):
                        sharing_policies_by_region[r]["organizations"].append(
                            organization
                        )
                else:
                    account_id = account.get("account_id")
                    if account_id not in sharing_policies_by_region[r]["accounts"]:
                        sharing_policies_by_region[r]["accounts"].append(account_id)

        return sharing_policies_by_region

    def get_shares_by_region_portfolio_account(self, puppet_account_id, section):
        shares_by_region_portfolio_account = {}
        configuration = {}

        for launch_name, launch_details in self.get(section, {}).items():
            portfolio = launch_details.get("portfolio")
            tasks = self.get_task_defs_from_details(
                puppet_account_id, launch_name, configuration, section,
            )
            for task in tasks:
                account_id = task.get("account_id")
                region = task.get("region")
                if shares_by_region_portfolio_account.get(region) is None:
                    shares_by_region_portfolio_account[region] = {}
                if shares_by_region_portfolio_account[region].get(portfolio) is None:
                    shares_by_region_portfolio_account[region][portfolio] = {}
                result = self.get_account(account_id)
                result[section] = launch_details
                shares_by_region_portfolio_account[region][portfolio][
                    account_id
                ] = result
        return shares_by_region_portfolio_account

    def get_accounts_by_region(self):
        accounts_by_region = {}
        for account in self.get("accounts"):
            account_regions = list()
            account_regions += account.get("enabled", [])
            account_regions += account.get("regions_enabled", [])
            account_regions += account.get("enabled_regions", [])
            account_regions.append(account.get("default_region"))
            for r in account_regions:
                if accounts_by_region.get(r) is None:
                    accounts_by_region[r] = []
                accounts_by_region[r].append(account)
        return accounts_by_region

    def get_task_defs_from_details(
        self,
        puppet_account_id,
        launch_name,
        configuration,
        launch_or_spoke_local_portfolio,
    ):
        launch_details = self.get(launch_or_spoke_local_portfolio).get(launch_name)
        accounts = self.get("accounts")
        if launch_details is None:
            raise Exception(f"launch_details is None for {launch_name}")
        if launch_or_spoke_local_portfolio == "lambda-invocations":
            deploy_to = launch_details.get("invoke_for")
        if launch_or_spoke_local_portfolio == constants.SERVICE_CONTROL_POLICIES:
            deploy_to = launch_details.get("apply_to")
        elif launch_or_spoke_local_portfolio == "launches":
            deploy_to = launch_details.get("deploy_to")
        elif launch_or_spoke_local_portfolio == "spoke-local-portfolios":
            deploy_to = launch_details.get("deploy_to") or launch_details.get(
                "share_with"
            )
        task_defs = []
        for tag_list_item in deploy_to.get("tags", []):
            for account in accounts:
                for tag in account.get("tags", []):
                    if tag == tag_list_item.get("tag"):
                        tag_account_def = deepcopy(configuration)
                        tag_account_def["account_id"] = account.get("account_id")
                        tag_account_def["account_parameters"] = account.get(
                            "parameters", {}
                        )

                        regions = tag_list_item.get("regions", "default_region")
                        if isinstance(regions, str):
                            if regions in [
                                "enabled",
                                "regions_enabled",
                                "enabled_regions",
                            ]:
                                for region_enabled in account.get("regions_enabled"):
                                    region_tag_account_def = deepcopy(tag_account_def)
                                    region_tag_account_def["region"] = region_enabled
                                    task_defs.append(region_tag_account_def)
                            elif regions == "default_region":
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def["region"] = account.get(
                                    "default_region"
                                )
                                task_defs.append(region_tag_account_def)
                            elif regions == "all":
                                all_regions = regions_configured
                                for region_enabled in all_regions:
                                    region_tag_account_def = deepcopy(tag_account_def)
                                    region_tag_account_def["region"] = region_enabled
                                    task_defs.append(region_tag_account_def)
                            else:
                                raise Exception(
                                    f"Unsupported regions {regions} setting for launch: {launch_name}"
                                )
                        elif isinstance(regions, list):
                            for region in regions:
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def["region"] = region
                                task_defs.append(region_tag_account_def)
                        elif isinstance(regions, tuple):
                            for region in regions:
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def["region"] = region
                                task_defs.append(region_tag_account_def)
                        else:
                            raise Exception(
                                f"Unexpected regions of {regions} set for launch {launch_name}"
                            )

        for account_list_item in deploy_to.get("accounts", []):
            for account in accounts:
                if account.get("account_id") == account_list_item.get("account_id"):
                    account_account_def = deepcopy(configuration)
                    account_account_def["account_id"] = account.get("account_id")
                    account_account_def["account_parameters"] = account.get(
                        "parameters", {}
                    )

                    regions = account_list_item.get("regions", "default_region")
                    if isinstance(regions, str):
                        if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                            for region_enabled in account.get("regions_enabled"):
                                region_account_account_def = deepcopy(
                                    account_account_def
                                )
                                region_account_account_def["region"] = region_enabled
                                task_defs.append(region_account_account_def)
                        elif regions in ["default_region"]:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def["region"] = account.get(
                                "default_region"
                            )
                            task_defs.append(region_account_account_def)
                        elif regions in ["all"]:
                            all_regions = regions_configured
                            for region_enabled in all_regions:
                                region_account_account_def = deepcopy(
                                    account_account_def
                                )
                                region_account_account_def["region"] = region_enabled
                                task_defs.append(region_account_account_def)
                        else:
                            raise Exception(
                                f"Unsupported regions {regions} setting for launch: {launch_name}"
                            )

                    elif isinstance(regions, list):
                        for region in regions:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def["region"] = region
                            task_defs.append(region_account_account_def)
                    elif isinstance(regions, tuple):
                        for region in regions:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def["region"] = region
                            task_defs.append(region_account_account_def)
                    else:
                        raise Exception(
                            f"Unexpected regions of {regions} set for launch {launch_name}"
                        )
        return task_defs


def create_minimal_manifest(manifest):
    minimal_manifest = deepcopy(manifest)
    # minimal_manifest[constants.ACCOUNTS] = dict()
    minimal_manifest[constants.LAUNCHES] = dict()
    minimal_manifest[constants.STACKS] = dict()
    minimal_manifest[constants.SPOKE_LOCAL_PORTFOLIOS] = dict()
    minimal_manifest[constants.LAMBDA_INVOCATIONS] = dict()
    minimal_manifest[constants.ASSERTIONS] = dict()
    minimal_manifest[constants.SERVICE_CONTROL_POLICIES] = dict()
    minimal_manifest[constants.TAG_POLICIES] = dict()
    minimal_manifest[constants.APPS] = dict()
    minimal_manifest[constants.WORKSPACES] = dict()
    return minimal_manifest


def convert_to_graph(expanded_manifest, G):
    for section in constants.ALL_SECTION_NAMES:
        for item_name, item_details in expanded_manifest.get(section, {}).items():
            uid = f"{section}|{item_name}"
            data = dict(section=section, item_name=item_name,)
            data.update(item_details)
            G.add_nodes_from(
                [(uid, data),]
            )

    for section in constants.ALL_SECTION_NAMES:
        for item_name, item_details in expanded_manifest.get(section, {}).items():
            uid = f"{section}|{item_name}"
            for d in item_details.get("depends_on", []):
                if isinstance(d, str):
                    G.add_edge(uid, f"{constants.LAUNCHES}|{d}")
                else:
                    G.add_edge(
                        uid,
                        f"{constants.SECTION_SINGULAR_TO_PLURAL.get(d.get('type'))}|{d.get('name')}",
                    )
    return G


def explode(expanded_manifest):
    G = convert_to_graph(expanded_manifest, nx.Graph())

    S = [G.subgraph(c).copy() for c in nx.connected_components(G)]
    exploded = list()
    for s in S:
        m = create_minimal_manifest(expanded_manifest)
        for node in s.nodes(data=True):
            data = deepcopy(node[1])
            del data["section"]
            del data["item_name"]
            m[node[1].get("section")][node[1].get("item_name")] = data
        exploded.append(m)
    return exploded


def isolate(expanded_manifest, subset):
    section = subset["section"]
    item = subset["item"]
    uid = f"{section}|{item}"

    m = create_minimal_manifest(expanded_manifest)
    G = convert_to_graph(expanded_manifest, nx.DiGraph())
    node = G.nodes.get(uid)
    data = deepcopy(node)
    del data["section"]
    del data["item_name"]
    m[node.get("section")][node.get("item_name")] = data

    if subset.get("include_dependencies", False):
        click.echo("Including dependencies")
        for dependency in nx.edge_dfs(G, uid, orientation="original"):
            link, dependency_name, direction = dependency
            node = G.nodes.get(dependency_name)
            data = deepcopy(node)
            del data["section"]
            del data["item_name"]
            m[node.get("section")][node.get("item_name")] = data

    if subset.get("include_reverse_dependencies", False):
        click.echo("Including reverse dependencies")
        for reverse_dependency in nx.edge_dfs(G, uid, orientation="reverse"):
            reverse_dependency_name, link, direction = reverse_dependency
            node = G.nodes.get(reverse_dependency_name)
            data = deepcopy(node)
            del data["section"]
            del data["item_name"]
            m[node.get("section")][node.get("item_name")] = data

            for dependency in nx.edge_dfs(
                G, reverse_dependency_name, orientation="original"
            ):
                link, dependency_name, direction = dependency
                node = G.nodes.get(dependency_name)
                data = deepcopy(node)
                del data["section"]
                del data["item_name"]
                m[node.get("section")][node.get("item_name")] = data

    return m


def parse_conditions(manifest):
    for section_name in constants.SECTIONS_THAT_SUPPORT_CONDITIONS:
        for item_name, item in manifest.get(section_name, {}).items():
            if item.get("condition"):
                if isinstance(item.get("condition"), str):
                    condition = manifest.get("conditions").get(item.get("condition"))
                    if not condition.get_result():
                        manifest[section_name][item_name][
                            constants.MANIFEST_STATUS_FIELD_NAME
                        ] = constants.MANIFEST_STATUS_FIELD_VALUE_IGNORED
                        logger.info(
                            f"Removed {item_name} from {section_name} because condition ({item.get('condition')}) evaluated to false"
                        )
                else:
                    should_ignore = True
                    for condition_to_check in item.get("condition"):
                        condition = manifest.get("conditions").get(condition_to_check)
                        if condition.get_result():
                            should_ignore = False
                    if should_ignore:
                        manifest[section_name][item_name][
                            constants.MANIFEST_STATUS_FIELD_NAME
                        ] = constants.MANIFEST_STATUS_FIELD_VALUE_IGNORED
                        logger.info(
                            f"Removed {item_name} from {section_name} because condition ({item.get('condition')}) evaluated to false"
                        )
    return manifest


def rewrite_organizational_units(manifest, conversions, client):
    for item_name, item in manifest.get(constants.ORGANIZATIONAL_UNITS, {}).items():
        path = item.get("path")
        if not item.get("parent_ou_id"):
            parent_path = os.path.dirname(path)
            if conversions.get(parent_path):
                item["parent_ou_id"] = conversions.get(parent_path)
        if not item.get("name"):
            item["name"] = os.path.basename(path)

    return manifest
