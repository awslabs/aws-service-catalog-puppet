import yaml
import logging

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


def group_by_product(launches):
    logger.info('Grouping launches by product')
    launches_by_product = {}
    for launch_name, launch_details in launches.items():
        product = launch_details.get('product')
        if launches_by_product.get(product) is None:
            launches_by_product[product] = []
        launch_details['launch_name'] = launch_name
        launches_by_product[product].append(launch_details)
    logger.info('Finished grouping launches by product')
    return launches_by_product


def generate_launch_map(accounts, launches_by_account, launches_by_tag):
    logger.info('Generating launch map')
    deployment_map = {}
    for account in accounts:
        account_id = account.get('account_id')
        deployment_map[account_id] = account
        launches = account['launches'] = {}
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


def build_deployment_map(manifest):
    accounts = manifest.get('accounts')
    launches = manifest.get('launches')

    verify_no_ous_in_manifest(accounts)

    launches_by_product = group_by_product(launches)
    # check_for_duplicate_products_in_launches(launches_by_product)
    launches_by_tag = group_by_tag(launches)
    launches_by_account = group_by_account(launches)

    return generate_launch_map(
        accounts,
        launches_by_account,
        launches_by_tag,
    )


def verify_no_ous_in_manifest(accounts):
    for account in accounts:
        if account.get('account_id') is None:
            raise Exception("{} account object does not have an account_id".format(account.get('name')))


def check_for_duplicate_products_in_launches(launches_by_product):
    logger.info('Checking for duplicate products by tag')
    for product_name, product_launches in launches_by_product.items():
        tags_seen = {}
        for product_launch in product_launches:
            for tag in product_launch.get('deploy_to').get('tags', []):
                tag_name = tag.get('tag')
                if tags_seen.get(tag_name) is None:
                    tags_seen[tag_name] = product_launch
                else:
                    raise Exception(
                        "Cannot process {}.  Already added {} because of tag: {}".format(
                            product_launch.get('launch_name'),
                            tags_seen[tag_name].get('launch_name'),
                            tag_name
                        )
                    )
    logger.info('Finished checking for duplicate products by tag')

    logger.info('Checking for duplicate products by account listed twice')
    for product_name, product_launches in launches_by_product.items():
        accounts_seen = {}
        for product_launch in product_launches:
            for account in product_launch.get('deploy_to').get('accounts', []):
                account_id = account.get('account_id')
                if accounts_seen.get(account_id) is None:
                    accounts_seen[account_id] = product_launch
                else:
                    raise Exception(
                        "Cannot process {}. {} is already receiving product: {} as it was listed in launch: {}".format(
                            product_launch.get('launch_name'),
                            account_id,
                            accounts_seen[account_id].get('product'),
                            accounts_seen[account_id].get('launch_name'),
                        )
                    )
    logger.info('Finished checking for duplicate products by account listed twice')
