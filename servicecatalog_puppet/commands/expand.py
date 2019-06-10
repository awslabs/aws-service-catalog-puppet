from copy import deepcopy

from servicecatalog_puppet.macros import macros
import json

import logging

logger = logging.getLogger(__file__)


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


def do_expand(manifest, client):
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

    for launch_name, launch_details in new_manifest.get('launches').items():
        for parameter_name, parameter_details in launch_details.get('parameters', {}).items():
            if parameter_details.get('macro'):
                macro_to_run = macros.get(parameter_details.get('macro').get('method'))
                result = macro_to_run(client, parameter_details.get('macro').get('args'))
                parameter_details['default'] = result
                del parameter_details['macro']

    return new_manifest
