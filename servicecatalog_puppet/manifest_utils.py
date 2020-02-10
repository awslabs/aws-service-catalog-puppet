import yaml
import logging
import json
from copy import deepcopy

from servicecatalog_puppet import config
from servicecatalog_puppet.macros import macros
from servicecatalog_puppet import constants

logger = logging.getLogger(__file__)


def load(f):
    return yaml.safe_load(f.read())


def expand_manifest(manifest, client):
    new_manifest = deepcopy(manifest)
    temp_accounts = []

    logger.info('Starting the expand')

    for account in manifest.get('accounts'):
        if account.get('account_id'):
            logger.info("Found an account: {}".format(account.get('account_id')))
            temp_accounts.append(account)
        elif account.get('ou'):
            ou = account.get('ou')
            logger.info("Found an ou: {}".format(ou))
            if ou.startswith('/'):
                temp_accounts += expand_path(account, client)
            else:
                temp_accounts += expand_ou(account, client)

    for parameter_name, parameter_details in new_manifest.get('parameters', {}).items():
        if parameter_details.get('macro'):
            macro_to_run = macros.get(parameter_details.get('macro').get('method'))
            result = macro_to_run(client, parameter_details.get('macro').get('args'))
            parameter_details['default'] = result
            del parameter_details['macro']

    accounts_by_id = {}
    for account in temp_accounts:
        for parameter_name, parameter_details in account.get('parameters', {}).items():
            if parameter_details.get('macro'):
                macro_to_run = macros.get(parameter_details.get('macro').get('method'))
                result = macro_to_run(client, parameter_details.get('macro').get('args'))
                parameter_details['default'] = result
                del parameter_details['macro']

        account_id = account.get('account_id')
        if account.get('append') or account.get('overwrite'):
            if account.get('default_region') or account.get('regions_enabled') or account.get('tags'):
                raise Exception(
                    f"{account_id}: If using append or overwrite you cannot set default_region, regions_enabled or tags"
                )

        if accounts_by_id.get(account_id) is None:
            accounts_by_id[account_id] = account
        else:
            stored_account = accounts_by_id[account_id]
            stored_account.update(account)

            if stored_account.get('append'):
                append = stored_account.get('append')
                for tag in append.get('tags', []):
                    stored_account.get('tags').append(tag)
                for region_enabled in append.get('regions_enabled', []):
                    stored_account.get('regions_enabled').append(region_enabled)
                del stored_account['append']

            elif stored_account.get('overwrite'):
                overwrite = stored_account.get('overwrite')
                if overwrite.get('tags'):
                    stored_account['tags'] = overwrite.get('tags')
                if overwrite.get('regions_enabled'):
                    stored_account['regions_enabled'] = overwrite.get('regions_enabled')
                if overwrite.get('default_region'):
                    stored_account['default_region'] = overwrite.get('default_region')
                del stored_account['overwrite']

            else:
                raise Exception(
                    f"Account {account_id} has been seen twice without using append or overwrite"
                )
    new_manifest['accounts'] = list(accounts_by_id.values())

    for launch_name, launch_details in new_manifest.get(constants.LAUNCHES, {}).items():
        for parameter_name, parameter_details in launch_details.get('parameters', {}).items():
            if parameter_details.get('macro'):
                macro_to_run = macros.get(parameter_details.get('macro').get('method'))
                result = macro_to_run(client, parameter_details.get('macro').get('args'))
                parameter_details['default'] = result
                del parameter_details['macro']

    return new_manifest


def expand_path(account, client):
    ou = client.convert_path_to_ou(account.get('ou'))
    account['ou'] = ou
    return expand_ou(account, client)


def expand_ou(original_account, client):
    expanded = []
    exclusions = original_account.get('exclude', {}).get('accounts', [])
    ou_exclusions = original_account.get('exclude', {}).get('ous', [])
    for ou_exclusion in ou_exclusions:
        if ou_exclusion.startswith('/'):
            ou_id = client.convert_path_to_ou(ou_exclusion)
        else:
            ou_id = ou_exclusion
        children = client.list_children_nested(ParentId=ou_id, ChildType='ACCOUNT')
        for child in children:
            logger.info(f"Adding {child.get('Id')} to the exclusion list as it was in the ou {ou_exclusion}")
            exclusions.append(child.get('Id'))

    response = client.list_children_nested(ParentId=original_account.get('ou'), ChildType='ACCOUNT')
    for result in response:
        new_account_id = result.get('Id')
        if new_account_id in exclusions:
            logger.info(f"Skipping {new_account_id} as it is in the exclusion list")
            continue
        response = client.describe_account(AccountId=new_account_id)
        new_account = deepcopy(original_account)
        del new_account['ou']
        if response.get('Account').get('Status') == "ACTIVE":
            if response.get('Account').get('Name') is not None:
                new_account['name'] = response.get('Account').get('Name')
            new_account['email'] = response.get('Account').get('Email')
            new_account['account_id'] = new_account_id
            new_account['expanded_from'] = original_account.get('ou')
            new_account['organization'] = response.get('Account').get('Arn').split(":")[5].split("/")[1]
            expanded.append(new_account)
        else:
            logger.info(f"Skipping account as it is not ACTIVE: {json.dumps(response.get('Account'), default=str)}")
    return expanded


def get_configuration_overrides(manifest, launch_details):
    configuration = {}
    if manifest.get('configuration'):
        if manifest.get('configuration').get('retry_count'):
            configuration['retry_count'] = manifest.get('configuration').get('retry_count')
    if launch_details.get('configuration'):
        if launch_details.get('configuration').get('retry_count'):
            configuration['retry_count'] = launch_details.get('configuration').get('retry_count')
        if launch_details.get('configuration').get('requested_priority'):
            configuration['requested_priority'] = int(launch_details.get('configuration').get('requested_priority'))
    return configuration


def get_actions_from(name, launch_details, pre_or_post, actions, launch_or_spoke_local_portfolio):
    result = []
    for provision_action in launch_details.get(f'{pre_or_post}_actions', []):
        action = deepcopy(actions.get(provision_action.get('name')))
        action.update(provision_action)
        action['source'] = name
        action['phase'] = pre_or_post
        action['source_type'] = launch_or_spoke_local_portfolio
        result.append(action)
    return result


def get_task_defs_from_details(launch_details, accounts, include_expanded_from, launch_name, configuration):
    deploy_to = launch_details.get('deploy_to')
    task_defs = []
    for tag_list_item in deploy_to.get('tags', []):
        for account in accounts:
            for tag in account.get('tags', []):
                if tag == tag_list_item.get('tag'):
                    tag_account_def = deepcopy(configuration)
                    tag_account_def['account_id'] = account.get('account_id')
                    if include_expanded_from:
                        tag_account_def['expanded_from'] = account.get('expanded_from')
                        tag_account_def['organization'] = account.get('organization')
                    tag_account_def['account_parameters'] = account.get('parameters', {})

                    regions = tag_list_item.get('regions', 'default_region')
                    if isinstance(regions, str):
                        if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                            for region_enabled in account.get('regions_enabled'):
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = region_enabled
                                task_defs.append(region_tag_account_def)
                        elif regions == 'default_region':
                            region_tag_account_def = deepcopy(tag_account_def)
                            region_tag_account_def['region'] = account.get('default_region')
                            task_defs.append(region_tag_account_def)
                        elif regions == "all":
                            all_regions = config.get_regions()
                            for region_enabled in all_regions:
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = region_enabled
                                task_defs.append(region_tag_account_def)
                        else:
                            raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")
                    elif isinstance(regions, list):
                        for region in regions:
                            region_tag_account_def = deepcopy(tag_account_def)
                            region_tag_account_def['region'] = region
                            task_defs.append(region_tag_account_def)
                    elif isinstance(regions, tuple):
                        for region in regions:
                            region_tag_account_def = deepcopy(tag_account_def)
                            region_tag_account_def['region'] = region
                            task_defs.append(region_tag_account_def)
                    else:
                        raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

    for account_list_item in deploy_to.get('accounts', []):
        for account in accounts:
            if account.get('account_id') == account_list_item.get('account_id'):
                account_account_def = deepcopy(configuration)
                account_account_def['account_id'] = account.get('account_id')
                if include_expanded_from:
                    account_account_def['expanded_from'] = account.get('expanded_from')
                    account_account_def['organization'] = account.get('organization')
                account_account_def['account_parameters'] = account.get('parameters', {})

                regions = account_list_item.get('regions', 'default_region')
                if isinstance(regions, str):
                    if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                        for region_enabled in account.get('regions_enabled'):
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = region_enabled
                            task_defs.append(region_account_account_def)
                    elif regions in ["default_region"]:
                        region_account_account_def = deepcopy(account_account_def)
                        region_account_account_def['region'] = account.get('default_region')
                        task_defs.append(region_account_account_def)
                    elif regions in ["all"]:
                        all_regions = config.get_regions()
                        for region_enabled in all_regions:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = region_enabled
                            task_defs.append(region_account_account_def)
                    else:
                        raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")

                elif isinstance(regions, list):
                    for region in regions:
                        region_account_account_def = deepcopy(account_account_def)
                        region_account_account_def['region'] = region
                        task_defs.append(region_account_account_def)
                elif isinstance(regions, tuple):
                    for region in regions:
                        region_account_account_def = deepcopy(account_account_def)
                        region_account_account_def['region'] = region
                        task_defs.append(region_account_account_def)
                else:
                    raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")
    return task_defs
