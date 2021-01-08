import configparser
import os

import yaml
import logging
import json
from copy import deepcopy

from servicecatalog_puppet import config
from servicecatalog_puppet.macros import macros
from servicecatalog_puppet import constants


logger = logging.getLogger(__file__)


def load(f, puppet_account_id):
    manifest_name = f.name
    manifest = {
        "schema": "puppet-2019-04-01",
        "parameters": {},
        "accounts": [],
        "launches": {},
        "spoke-local-portfolios": {},
    }
    manifest.update(yaml.safe_load(f.read()))
    d = os.path.dirname(os.path.abspath(f.name))

    extendable = ["parameters", "launches", "spoke-local-portfolios"]
    for t in extendable:
        t_path = f"{d}{os.path.sep}{t}"
        if os.path.exists(t_path):
            for f in os.listdir(t_path):
                with open(f"{t_path}{os.path.sep}{f}", "r") as file:
                    manifest[t].update(yaml.safe_load(file.read()))

    if os.path.exists(f"{d}{os.path.sep}manifests"):
        for f in os.listdir(f"{d}{os.path.sep}manifests"):
            with open(f"{d}{os.path.sep}manifests{os.path.sep}{f}", "r") as file:
                ext = yaml.safe_load(file.read())
                for t in extendable:
                    manifest[t].update(ext.get(t, {}))

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
            for name, value in parser["launches"].items():
                launch_name, property_name = name.split(".")
                if property_name != "version":
                    raise Exception(
                        "You can only specify a version in the properties file"
                    )
                manifest["launches"][launch_name][property_name] = value
    for launch_name, launch_details in manifest.get("launches").items():
        if launch_details.get("execution") is None:
            launch_details["execution"] = constants.EXECUTION_MODE_DEFAULT
    return manifest


def expand_manifest(manifest, client):
    new_manifest = deepcopy(manifest)
    temp_accounts = []

    logger.info("Starting the expand")

    for account in manifest.get("accounts"):
        if account.get("account_id"):
            logger.info("Found an account: {}".format(account.get("account_id")))
            temp_accounts.append(account)
        elif account.get("ou"):
            ou = account.get("ou")
            logger.info("Found an ou: {}".format(ou))
            if ou.startswith("/"):
                temp_accounts += expand_path(account, client)
            else:
                temp_accounts += expand_ou(account, client)

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
            stored_account = accounts_by_id[account_id]
            stored_account.update(account)

            if stored_account.get("append"):
                append = stored_account.get("append")
                for tag in append.get("tags", []):
                    stored_account.get("tags").append(tag)
                for region_enabled in append.get("regions_enabled", []):
                    stored_account.get("regions_enabled").append(region_enabled)
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

            else:
                raise Exception(
                    f"Account {account_id} has been seen twice without using append or overwrite"
                )
    new_manifest["accounts"] = list(accounts_by_id.values())

    for launch_name, launch_details in new_manifest.get(constants.LAUNCHES, {}).items():
        for parameter_name, parameter_details in launch_details.get(
            "parameters", {}
        ).items():
            if parameter_details.get("macro"):
                macro_to_run = macros.get(parameter_details.get("macro").get("method"))
                result = macro_to_run(
                    client, parameter_details.get("macro").get("args")
                )
                parameter_details["default"] = result
                del parameter_details["macro"]

    return new_manifest


def expand_path(account, client):
    ou = client.convert_path_to_ou(account.get("ou"))
    account["ou"] = ou
    return expand_ou(account, client)


def expand_ou(original_account, client):
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
        response = client.describe_account(AccountId=new_account_id)
        new_account = deepcopy(original_account)
        del new_account["ou"]
        if response.get("Account").get("Status") == "ACTIVE":
            if response.get("Account").get("Name") is not None:
                new_account["name"] = response.get("Account").get("Name")
            new_account["email"] = response.get("Account").get("Email")
            new_account["account_id"] = new_account_id
            new_account["expanded_from"] = original_account.get("ou")
            new_account["organization"] = (
                response.get("Account").get("Arn").split(":")[5].split("/")[1]
            )
            expanded.append(new_account)
        else:
            logger.info(
                f"Skipping account as it is not ACTIVE: {json.dumps(response.get('Account'), default=str)}"
            )
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
            raise Exception(f"Could not find: {''+'/'.join(mapping)}")
        return result

    def get_actions_from(
        self, launch_name, pre_or_post, launch_or_spoke_local_portfolio
    ):
        logger.info(
            f"get_actions_from for {launch_or_spoke_local_portfolio}.{launch_name}"
        )
        launch_details = self.get(launch_or_spoke_local_portfolio).get(launch_name)
        actions = self.get("actions")
        result = list()
        for provision_action in launch_details.get(f"{pre_or_post}_actions", []):
            action = dict()
            action.update(actions.get(provision_action.get("name")))
            action.update(provision_action)
            action["source"] = launch_name
            action["phase"] = pre_or_post
            action["source_type"] = launch_or_spoke_local_portfolio
            result.append(action)
        return result

    def get_account(self, account_id):
        for account in self.get("accounts"):
            if account.get("account_id") == account_id:
                return account
        raise Exception(f"Could not find account: {account_id}")

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
        include_expanded_from = False
        for launch_name, launch_details in self.get(section, {}).items():
            portfolio = launch_details.get("portfolio")
            tasks = self.get_task_defs_from_details(
                puppet_account_id,
                include_expanded_from,
                launch_name,
                configuration,
                section,
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
        include_expanded_from,
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
                        if include_expanded_from:
                            tag_account_def["expanded_from"] = account.get(
                                "expanded_from"
                            )
                            tag_account_def["organization"] = account.get(
                                "organization"
                            )
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
                                all_regions = config.get_regions(puppet_account_id)
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
                    if include_expanded_from:
                        account_account_def["expanded_from"] = account.get(
                            "expanded_from"
                        )
                        account_account_def["organization"] = account.get(
                            "organization"
                        )
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
                            all_regions = config.get_regions(puppet_account_id)
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
