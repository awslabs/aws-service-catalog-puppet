import click
import yaml
import logging
import json
from copy import deepcopy

from servicecatalog_puppet.workflow import portfoliomanagement
from servicecatalog_puppet.workflow import provisioning
from servicecatalog_puppet import config
from servicecatalog_puppet.macros import macros
from servicecatalog_puppet import constants, aws

import progressbar

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

    logger.debug(temp_accounts)

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


def generate_launch_task_defs(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans, include_expanded_from=False,
        single_account=None, dry_run=False
):
    task_defs_by_launch_name = {}
    accounts = manifest.get('accounts', [])
    actions = manifest.get('actions', {})
    for launch_name, launch_details in manifest.get('launches', {}).items():
        logger.info(f"looking at {launch_name} in convert_manifest_into_task_defs_for_launches")
        pre_actions = []
        for provision_action in launch_details.get('pre_actions', []):
            action = deepcopy(actions.get(provision_action.get('name')))
            action.update(provision_action)
            action['source'] = launch_name
            action['phase'] = 'pre'
            action['source_type'] = 'launch'
            pre_actions.append(action)

        post_actions = []
        for provision_action in launch_details.get('post_actions', []):
            action = deepcopy(actions.get(provision_action.get('name')))
            action.update(provision_action)
            action['source'] = launch_name
            action['phase'] = 'post'
            action['source_type'] = 'launch'
            post_actions.append(action)

        logger.info(f'looking at {launch_name} and depends on is {launch_details.get("depends_on", [])}')

        task_def = {
            'launch_name': launch_name,
            'portfolio': launch_details.get('portfolio'),
            'product': launch_details.get('product'),
            'version': launch_details.get('version'),

            'puppet_account_id': puppet_account_id,

            'parameters': [],
            'ssm_param_inputs': [],
            'launch_parameters': launch_details.get('parameters', {}),
            'manifest_parameters': manifest.get('parameters', {}),

            'depends_on': launch_details.get('depends_on', []),
            'dependencies': [],
            'launch_dependencies': [],

            'retry_count': 0,
            'worker_timeout': launch_details.get('timeoutInSeconds', constants.DEFAULT_TIMEOUT),
            'ssm_param_outputs': launch_details.get('outputs', {}).get('ssm', []),
            'should_use_sns': should_use_sns,
            'should_use_product_plans': should_use_product_plans,
            'requested_priority': 0,

            'status': launch_details.get('status', constants.PROVISIONED),

            'pre_actions': pre_actions,
            'post_actions': post_actions,
        }

        if manifest.get('configuration'):
            if manifest.get('configuration').get('retry_count'):
                task_def['retry_count'] = manifest.get('configuration').get('retry_count')
        if launch_details.get('configuration'):
            if launch_details.get('configuration').get('retry_count'):
                task_def['retry_count'] = launch_details.get('configuration').get('retry_count')
            if launch_details.get('configuration').get('requested_priority'):
                task_def['requested_priority'] = int(launch_details.get('configuration').get('requested_priority'))


        logger.info(f'{launch_name}: 1')

        deploy_to = launch_details .get('deploy_to')
        for tag_list_item in deploy_to.get('tags', []):
            for account in accounts:
                for tag in account.get('tags', []):
                    if tag == tag_list_item.get('tag'):
                        tag_account_def = deepcopy(task_def)
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
                                    if task_defs_by_launch_name.get(launch_name) is None:
                                        task_defs_by_launch_name[launch_name] = []
                                    task_defs_by_launch_name[launch_name].append(region_tag_account_def)
                            elif regions == 'default_region':
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = account.get('default_region')
                                if task_defs_by_launch_name.get(launch_name) is None:
                                    task_defs_by_launch_name[launch_name] = []
                                task_defs_by_launch_name[launch_name].append(region_tag_account_def)

                            elif regions == "all":
                                all_regions = config.get_regions()
                                for region_enabled in all_regions:
                                    region_tag_account_def = deepcopy(tag_account_def)
                                    region_tag_account_def['region'] = region_enabled
                                    if task_defs_by_launch_name.get(launch_name) is None:
                                        task_defs_by_launch_name[launch_name] = []
                                    task_defs_by_launch_name[launch_name].append(region_tag_account_def)

                            else:
                                raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")
                        elif isinstance(regions, list):
                            for region in regions:
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = region
                                if task_defs_by_launch_name.get(launch_name) is None:
                                    task_defs_by_launch_name[launch_name] = []
                                task_defs_by_launch_name[launch_name].append(region_tag_account_def)

                        else:
                            raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

        logger.info(f'{launch_name}: 2')
        for account_list_item in deploy_to.get('accounts', []):
            for account in accounts:
                if account.get('account_id') == account_list_item.get('account_id'):
                    account_account_def = deepcopy(task_def)
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
                                if task_defs_by_launch_name.get(launch_name) is None:
                                    task_defs_by_launch_name[launch_name] = []
                                task_defs_by_launch_name[launch_name].append(region_account_account_def)
                        elif regions in ["default_region"]:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = account.get('default_region')
                            if task_defs_by_launch_name.get(launch_name) is None:
                                task_defs_by_launch_name[launch_name] = []
                            task_defs_by_launch_name[launch_name].append(region_account_account_def)
                        elif regions in ["all"]:
                            all_regions = config.get_regions()
                            for region_enabled in all_regions:
                                region_account_account_def = deepcopy(account_account_def)
                                region_account_account_def['region'] = region_enabled
                                if task_defs_by_launch_name.get(launch_name) is None:
                                    task_defs_by_launch_name[launch_name] = []
                                task_defs_by_launch_name[launch_name].append(region_account_account_def)
                        else:
                            raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")

                    elif isinstance(regions, list):
                        for region in regions:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = region
                            if task_defs_by_launch_name.get(launch_name) is None:
                                task_defs_by_launch_name[launch_name] = []
                            task_defs_by_launch_name[launch_name].append(region_account_account_def)
                    else:
                        raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")
    return task_defs_by_launch_name


def generate_launch_tasks(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans, include_expanded_from=False,
        single_account=None, dry_run=False
):
    # Create all task defs and group by launch name
    task_defs = []
    task_defs_by_launch_name = generate_launch_task_defs(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans, include_expanded_from,
        single_account, dry_run
    )
    # Create launch tasks and assign taskdefs
    launch_tasks = {}
    logger.info('arghhh')
    for task_defs_launch_name, task_defs in task_defs_by_launch_name.items():
        logger.info(task_defs)
        launch_tasks[task_defs_launch_name] = provisioning.LaunchTask(
            launch_name=task_defs_launch_name,
            task_defs=task_defs,
            is_dry_run=dry_run,
        )

    n_task_defs = len(task_defs)
    bar = progressbar.ProgressBar(
        maxval=n_task_defs,
        widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()]
    )
    counter = 1
    bar.start()
    click.echo(f'about to wire up dependencies of tasks {n_task_defs}')
    for task_def in task_defs:
        bar.update(counter)
        counter += 1
        for launch_dependency in task_def.get('depends_on', []):
            task_def['launch_dependencies'].append(
                deepcopy(launch_tasks.get(launch_dependency).param_kwargs)
            )
    bar.finish()
    return list(launch_tasks.values())


def generate_spoke_local_portfolios_task_defs(
        manifest, puppet_account_id, should_use_sns
):
    tasks_by_spoke_local_portfolios = {}
    accounts = manifest.get('accounts', [])
    actions = manifest.get('actions', {})

    for launch_name, launch_details in manifest.get('spoke-local-portfolios', {}).items():
        logger.info(f"Looking at {launch_name} in generate_spoke_local_portfolios_task_defs")
        pre_actions = []
        for provision_action in launch_details.get('pre_actions', []):
            action = deepcopy(actions.get(provision_action.get('name')))
            action.update(provision_action)
            action['source'] = launch_name
            action['phase'] = 'pre'
            action['source_type'] = 'spoke-local-portfolios'
            pre_actions.append(action)

        post_actions = []
        for provision_action in launch_details.get('post_actions', []):
            action = deepcopy(actions.get(provision_action.get('name')))
            action.update(provision_action)
            action['source'] = launch_name
            action['phase'] = 'post'
            action['source_type'] = 'spoke-local-portfolios'
            post_actions.append(action)

        task_def = {
            'launch_details': launch_details,
            'puppet_account_id': puppet_account_id,
            'should_use_sns': should_use_sns,
            'pre_actions': pre_actions,
            'post_actions': post_actions,
        }

        if manifest.get('configuration'):
            if manifest.get('configuration').get('retry_count'):
                task_def['retry_count'] = manifest.get('configuration').get('retry_count')
        if launch_details.get('configuration'):
            if launch_details.get('configuration').get('retry_count'):
                task_def['retry_count'] = launch_details.get('configuration').get('retry_count')
            if launch_details.get('configuration').get('requested_priority'):
                task_def['requested_priority'] = int(launch_details.get('configuration').get('requested_priority'))

        deploy_to = launch_details.get('deploy_to')
        for tag_list_item in deploy_to.get('tags', []):
            for account in accounts:
                for tag in account.get('tags', []):
                    if tag == tag_list_item.get('tag'):
                        tag_account_def = deepcopy(task_def)
                        tag_account_def['account_id'] = account.get('account_id')
                        tag_account_def['expanded_from'] = account.get('expanded_from')
                        tag_account_def['organization'] = account.get('organization')

                        regions = tag_list_item.get('regions', 'default_region')
                        if isinstance(regions, str):
                            if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                                for region_enabled in account.get('regions_enabled'):
                                    region_tag_account_def = deepcopy(tag_account_def)
                                    region_tag_account_def['region'] = region_enabled
                                    if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                        tasks_by_spoke_local_portfolios[launch_name] = []
                                    tasks_by_spoke_local_portfolios[launch_name].append(
                                        region_tag_account_def
                                    )
                            elif regions == 'default_region':
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = account.get('default_region')
                                if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                    tasks_by_spoke_local_portfolios[launch_name] = []
                                tasks_by_spoke_local_portfolios[launch_name].append(
                                    region_tag_account_def
                                )
                            elif regions == "all":
                                all_regions = config.get_regions()
                                for region_enabled in all_regions:
                                    region_tag_account_def = deepcopy(tag_account_def)
                                    region_tag_account_def['region'] = region_enabled
                                    if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                        tasks_by_spoke_local_portfolios[launch_name] = []
                                    tasks_by_spoke_local_portfolios[launch_name].append(
                                        region_tag_account_def
                                    )
                            else:
                                raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")
                        elif isinstance(regions, list):
                            for region in regions:
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = region
                                if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                    tasks_by_spoke_local_portfolios[launch_name] = []
                                tasks_by_spoke_local_portfolios[launch_name].append(
                                    region_tag_account_def
                                )
                        else:
                            raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

        for account_list_item in deploy_to.get('accounts', []):
            for account in accounts:
                if account.get('account_id') == account_list_item.get('account_id'):
                    account_account_def = deepcopy(task_def)
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
                                if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                    tasks_by_spoke_local_portfolios[launch_name] = []
                                tasks_by_spoke_local_portfolios[launch_name].append(
                                    region_account_account_def
                                )
                        elif regions == 'default_region':
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = account.get('default_region')
                            if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                tasks_by_spoke_local_portfolios[launch_name] = []
                            tasks_by_spoke_local_portfolios[launch_name].append(
                                region_account_account_def
                            )
                        elif regions == "all":
                            all_regions = config.get_regions()
                            for region_enabled in all_regions:
                                region_account_account_def = deepcopy(account_account_def)
                                region_account_account_def['region'] = region_enabled
                                if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                    tasks_by_spoke_local_portfolios[launch_name] = []
                                tasks_by_spoke_local_portfolios[launch_name].append(
                                    region_account_account_def
                                )
                        else:
                            raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")

                    elif isinstance(regions, list):
                        for region in regions:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = region
                            if tasks_by_spoke_local_portfolios.get(launch_name) is None:
                                tasks_by_spoke_local_portfolios[launch_name] = []
                            tasks_by_spoke_local_portfolios[launch_name].append(
                                region_account_account_def
                            )
                    else:
                        raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")
    return tasks_by_spoke_local_portfolios


def generate_spoke_local_portfolios_tasks(
        manifest, puppet_account_id, should_use_sns, is_dry_run
):
    tasks_by_spoke_local_portfolios = generate_spoke_local_portfolios_task_defs(
        manifest, puppet_account_id, should_use_sns
    )

    tasks_by_spoke_local_portfolios_tasks = {}
    for tasks_by_spoke_local_portfolio_name, tasks_by_spoke_local_portfolio in tasks_by_spoke_local_portfolios.items():
        logger.info(f"EEEPPPFF {tasks_by_spoke_local_portfolio_name}")
        tasks_by_spoke_local_portfolios_tasks[tasks_by_spoke_local_portfolio_name] = provisioning.SpokeLocalPortfolioTask(
            spoke_local_portfolio_name=tasks_by_spoke_local_portfolio_name,
            task_defs=tasks_by_spoke_local_portfolio,
            is_dry_run=is_dry_run,
        )
    return list(tasks_by_spoke_local_portfolios_tasks.values())
