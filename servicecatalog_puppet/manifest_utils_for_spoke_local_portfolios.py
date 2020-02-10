from copy import deepcopy
from servicecatalog_puppet import constants, config

from servicecatalog_puppet.workflow import provisioning
from servicecatalog_puppet.manifest_utils import get_actions_from, get_configuration_overrides, get_task_defs_from_details

import logging

logger = logging.getLogger(__file__)


def get_task_defs_from_details(launch_details, accounts, include_expanded_from, launch_name, configuration):
    tasks = []

    deploy_to = launch_details.get('deploy_to')
    for tag_list_item in deploy_to.get('tags', []):
        for account in accounts:
            for tag in account.get('tags', []):
                if tag == tag_list_item.get('tag'):
                    tag_account_def = deepcopy(configuration)
                    tag_account_def['account_id'] = account.get('account_id')
                    tag_account_def['expanded_from'] = account.get('expanded_from', '')
                    tag_account_def['organization'] = account.get('organization')

                    regions = tag_list_item.get('regions', 'default_region')
                    if isinstance(regions, str):
                        if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                            for region_enabled in account.get('regions_enabled'):
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = region_enabled
                                tasks.append(region_tag_account_def)
                        elif regions == 'default_region':
                            region_tag_account_def = deepcopy(tag_account_def)
                            region_tag_account_def['region'] = account.get('default_region')
                            tasks.append(region_tag_account_def)
                        elif regions == "all":
                            all_regions = config.get_regions()
                            for region_enabled in all_regions:
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = region_enabled
                                tasks.append(region_tag_account_def)
                        else:
                            raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")
                    elif isinstance(regions, list):
                        for region in regions:
                            region_tag_account_def = deepcopy(tag_account_def)
                            region_tag_account_def['region'] = region
                            tasks.append(region_tag_account_def)
                    elif isinstance(regions, tuple):
                        for region in regions:
                            region_tag_account_def = deepcopy(tag_account_def)
                            region_tag_account_def['region'] = region
                            tasks.append(region_tag_account_def)
                    else:
                        raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

    for account_list_item in deploy_to.get('accounts', []):
        for account in accounts:
            if account.get('account_id') == account_list_item.get('account_id'):
                account_account_def = deepcopy(configuration)
                account_account_def['account_id'] = account.get('account_id')
                account_account_def['expanded_from'] = account.get('expanded_from')
                account_account_def['organization'] = account.get('organization')
                # account_account_def['account_parameters'] = account.get('parameters', {})

                regions = account_list_item.get('regions', 'default_region')
                if isinstance(regions, str):
                    if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                        for region_enabled in account.get('regions_enabled'):
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = region_enabled
                            tasks.append(region_account_account_def)
                    elif regions == 'default_region':
                        region_account_account_def = deepcopy(account_account_def)
                        region_account_account_def['region'] = account.get('default_region')
                        tasks.append(region_account_account_def)
                    elif regions == "all":
                        all_regions = config.get_regions()
                        for region_enabled in all_regions:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = region_enabled
                            tasks.append(region_account_account_def)
                    else:
                        raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")

                elif isinstance(regions, list):
                    for region in regions:
                        region_account_account_def = deepcopy(account_account_def)
                        region_account_account_def['region'] = region
                        tasks.append(region_account_account_def)
                elif isinstance(regions, tuple):
                    for region in regions:
                        region_account_account_def = deepcopy(account_account_def)
                        region_account_account_def['region'] = region
                        tasks.append(region_account_account_def)
                else:
                    raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

    return tasks


def get_configuration_from_spoke_local_portfolio(manifest, spoke_local_portfolio_details, spoke_local_portfolio_name):
    configuration = {
        'spoke_local_portfolio_name': spoke_local_portfolio_name,
        'portfolio': spoke_local_portfolio_details.get('portfolio'),
        'associations': spoke_local_portfolio_details.get('associations', []),
        'constraints': spoke_local_portfolio_details.get('constraints', {}),
        'depends_on': spoke_local_portfolio_details.get('depends_on', []),
        'retry_count': spoke_local_portfolio_details.get('retry_count', 1),
        'requested_priority': spoke_local_portfolio_details.get('requested_priority', 0),
        'worker_timeout': spoke_local_portfolio_details.get('timeoutInSeconds', constants.DEFAULT_TIMEOUT),
    }
    configuration.update(
        get_configuration_overrides(manifest, spoke_local_portfolio_details)
    )
    return configuration


def generate_spoke_local_portfolios_tasks_for_spoke_local_portfolio(
        spoke_local_portfolio_name, manifest, puppet_account_id, should_use_sns, should_use_product_plans,
        include_expanded_from=False, single_account=None, is_dry_run=False,
):
    accounts = manifest.get('accounts', [])
    actions = manifest.get('actions', {})

    spoke_local_portfolio_details = manifest.get('spoke-local-portfolios').get(spoke_local_portfolio_name)

    configuration = get_configuration_from_spoke_local_portfolio(
        manifest, spoke_local_portfolio_details, spoke_local_portfolio_name
    )
    configuration['single_account'] = single_account
    configuration['is_dry_run'] = is_dry_run
    configuration['puppet_account_id'] = puppet_account_id
    configuration['should_use_sns'] = should_use_sns
    configuration['should_use_product_plans'] = should_use_product_plans

    task_defs = get_task_defs_from_details(
        spoke_local_portfolio_details, accounts, True, spoke_local_portfolio_name, configuration
    )
    return {
        'pre_actions': get_actions_from(
            spoke_local_portfolio_name, spoke_local_portfolio_details, 'pre', actions, 'spoke-local-portfolios'
        ),
        'post_actions': get_actions_from(
            spoke_local_portfolio_name, spoke_local_portfolio_details, 'post', actions, 'spoke-local-portfolios'
        ),
        'task_defs': task_defs
    }


def generate_spoke_local_portfolios_tasks(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans, include_expanded_from, single_account,
        is_dry_run
):
    return [
        provisioning.SpokeLocalPortfolioTask(
            spoke_local_portfolio_name=spoke_local_portfolio_name,
            manifest=manifest,
            puppet_account_id=puppet_account_id,
            should_use_sns=should_use_sns,
            should_use_product_plans=should_use_product_plans,
            include_expanded_from=include_expanded_from,
            single_account=single_account,
            is_dry_run=is_dry_run,
        ) for spoke_local_portfolio_name in manifest.get('spoke-local-portfolios', {}).keys()
    ]
