import yaml
import logging
import json
from copy import deepcopy

from servicecatalog_puppet.macros import macros
from servicecatalog_puppet import constants

logger = logging.getLogger(__file__)


def load(f):
    return yaml.safe_load(f.read())


def group_by_tag(launches):
    logger.info('Grouping launches by tag')
    launches_by_tag = {}
    for launch_name, launch_details in launches.items():
        launch_details['launch_name'] = launch_name
        launch_tags = launch_details.get('deploy_to').get('tags', [])
        for tag_detail in launch_tags:
            tag = tag_detail.get('tag')
            if launches_by_tag.get(tag) is None:
                launches_by_tag[tag] = []
            launches_by_tag[tag].append(launch_details)
    logger.info('Finished grouping launches by tag')
    return launches_by_tag


def group_by_account(launches):
    logger.info('Grouping launches by account')
    launches_by_account = {}
    for launch_name, launch_details in launches.items():
        launch_details['launch_name'] = launch_name
        launch_accounts = launch_details.get('deploy_to').get('accounts', [])
        for account_detail in launch_accounts:
            account_id = account_detail.get('account_id')
            if launches_by_account.get(account_id) is None:
                launches_by_account[account_id] = []
            launches_by_account[account_id].append(launch_details)
    logger.info('Finished grouping launches by account')
    return launches_by_account


def generate_launch_map(accounts, launches_by_account, launches_by_tag, section):
    logger.info('Generating launch map')
    deployment_map = {}
    for account in accounts:
        account_id = account.get('account_id')
        deployment_map[account_id] = account
        launches = account[section] = {}
        for launch in launches_by_account.get(account_id, []):
            launch['match'] = "account_match"
            launches[launch.get('launch_name')] = launch
        for tag in account.get('tags'):
            for launch in launches_by_tag.get(tag, []):
                launch['match'] = "tag_match"
                launch['matching_tag'] = tag
                launches[launch.get('launch_name')] = launch
    logger.info('Finished generating launch map')
    return deployment_map


def build_deployment_map(manifest, section):
    accounts = manifest.get('accounts')
    launches = manifest.get(section, {})

    verify_no_ous_in_manifest(accounts)

    launches_by_tag = group_by_tag(launches)
    launches_by_account = group_by_account(launches)

    return generate_launch_map(
        accounts,
        launches_by_account,
        launches_by_tag,
        section
    )


def verify_no_ous_in_manifest(accounts):
    for account in accounts:
        if account.get('account_id') is None:
            raise Exception("{} account object does not have an account_id".format(account.get('name')))


def expand_manifest(manifest, client):
    new_manifest = deepcopy(manifest)
    new_accounts = new_manifest['accounts'] = []

    logger.info('Starting the expand')

    for account in manifest.get('accounts'):
        if account.get('account_id'):
            logger.info("Found an account: {}".format(account.get('account_id')))
            new_accounts.append(account)
        elif account.get('ou'):
            ou = account.get('ou')
            logger.info("Found an ou: {}".format(ou))
            if ou.startswith('/'):
                new_accounts += expand_path(account, client)
            else:
                new_accounts += expand_ou(account, client)

    logger.debug(new_accounts)

    for parameter_name, parameter_details in new_manifest.get('parameters', {}).items():
        if parameter_details.get('macro'):
            macro_to_run = macros.get(parameter_details.get('macro').get('method'))
            result = macro_to_run(client, parameter_details.get('macro').get('args'))
            parameter_details['default'] = result
            del parameter_details['macro']

    for first_account in new_accounts:
        for parameter_name, parameter_details in first_account.get('parameters', {}).items():
            if parameter_details.get('macro'):
                macro_to_run = macros.get(parameter_details.get('macro').get('method'))
                result = macro_to_run(client, parameter_details.get('macro').get('args'))
                parameter_details['default'] = result
                del parameter_details['macro']

        times_seen = 0
        for second_account in new_accounts:
            if first_account.get('account_id') == second_account.get('account_id'):
                times_seen += 1
                if times_seen > 1:
                    message = "{} has been seen twice.".format(first_account.get('account_id'))
                    if first_account.get('expanded_from'):
                        message += "  It was included due to it being in the ou: {}".format(
                            first_account.get('expanded_from')
                        )
                    if second_account.get('expanded_from'):
                        message += "  It was included due to it being in the ou: {}".format(
                            second_account.get('expanded_from')
                        )
                    raise Exception(message)

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
    response = client.list_children_nested(ParentId=original_account.get('ou'), ChildType='ACCOUNT')
    for result in response:
        new_account_id = result.get('Id')
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
            logger.info(f"Skipping account as it is not ACTIVE: {json.dump(response.get('Account'), default=str)}")
    return expanded
