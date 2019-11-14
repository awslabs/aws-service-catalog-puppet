import yaml
import logging
import json
from copy import deepcopy

from .macros import macros
from . import constants, cli_command_helpers, luigi_tasks_and_targets, aws

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
            if not isinstance(account_detail.get('account_id'), str):
                account_detail['account_id'] = str(account_detail.get('account_id'))
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
        for tag in account.get('tags', []):
            for launch in launches_by_tag.get(tag, []):
                launch['match'] = "tag_match"
                launch['matching_tag'] = tag
                launches[launch.get('launch_name')] = launch
    logger.info('Finished generating launch map')
    return deployment_map


def build_deployment_map(manifest, section):
    accounts = manifest.get('accounts')
    for account_detail in accounts:
        if not isinstance(account_detail.get('account_id'), str):
            account_detail['account_id'] = str(account_detail.get('account_id'))
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
            logger.info(f"Skipping account as it is not ACTIVE: {json.dumps(response.get('Account'), default=str)}")
    return expanded


def convert_manifest_into_task_defs_for_launches(manifest, puppet_account_id, should_use_sns, should_use_product_plans):
    task_defs = []
    accounts = manifest.get('accounts', [])
    for launch_name, launch_details in manifest.get('launches', {}).items():
        logger.info(f"looking at {launch_name}")
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

            'retry_count': 0,
            'worker_timeout': launch_details.get('timeoutInSeconds', constants.DEFAULT_TIMEOUT),
            'ssm_param_outputs': launch_details.get('outputs', {}).get('ssm', []),
            'should_use_sns': should_use_sns,
            'should_use_product_plans': should_use_product_plans,
            'requested_priority': 0,

            'status': launch_details.get('status', constants.PROVISIONED),
        }

        if manifest.get('configuration'):
            if manifest.get('configuration').get('retry_count'):
                task_def['retry_count'] = manifest.get('configuration').get('retry_count')
        if launch_details.get('configuration'):
            if launch_details.get('configuration').get('retry_count'):
                task_def['retry_count'] = launch_details.get('configuration').get('retry_count')
            if launch_details.get('configuration').get('requested_priority'):
                task_def['requested_priority'] = int(launch_details.get('configuration').get('requested_priority'))

        deploy_to = launch_details .get('deploy_to')
        for tag_list_item in deploy_to.get('tags', []):
            for account in accounts:
                for tag in account.get('tags', []):
                    if tag == tag_list_item.get('tag'):
                        tag_account_def = deepcopy(task_def)
                        tag_account_def['account_id'] = account.get('account_id')
                        tag_account_def['account_parameters'] = account.get('parameters', {})

                        regions = tag_list_item.get('regions')
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
                                all_regions = cli_command_helpers.get_regions()
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
                        else:
                            raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

        for account_list_item in deploy_to.get('accounts', []):
            for account in accounts:
                if account.get('account_id') == account_list_item.get('account_id'):
                    account_account_def = deepcopy(task_def)
                    account_account_def['account_id'] = account.get('account_id')
                    account_account_def['account_parameters'] = account.get('parameters', {})

                    regions = account_list_item.get('regions')
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
                            all_regions = cli_command_helpers.get_regions()
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
                    else:
                        raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

    for task_def in task_defs:
        for depends_on_launch_name in task_def.get('depends_on', []):
            for task_def_2 in task_defs:
                if task_def_2.get('launch_name') == depends_on_launch_name:
                    task_def_2_copy = deepcopy(task_def_2)
                    del task_def_2_copy['depends_on']
                    task_def_2_copy['dependencies'] = []
                    task_def['dependencies'].append(task_def_2_copy)

    for task_def in task_defs:
        del task_def['depends_on']

    return task_defs


def convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
        account_id, region, launch_details,
        puppet_account_id, should_use_sns, launch_tasks
):
    dependencies = []
    for depend in launch_details.get('depends_on', []):
        for launch_task in launch_tasks:
            if isinstance(launch_task, luigi_tasks_and_targets.ProvisionProductTask):
                l_params = launch_task.to_str_params()
                if l_params.get('launch_name') == depend:
                    # dependencies.append(launch_task.param_args)
                    dependencies.append(launch_task.param_kwargs)
    hub_portfolio = aws.get_portfolio_for(
        launch_details.get('portfolio'), puppet_account_id, region
    )
    tasks_to_run = []
    create_spoke_local_portfolio_task_params = {
        'account_id': account_id,
        'region': region,
        'portfolio': launch_details.get('portfolio'),
        'provider_name': hub_portfolio.get('ProviderName'),
        'description': hub_portfolio.get('Description'),
    }
    create_spoke_local_portfolio_task = luigi_tasks_and_targets.CreateSpokeLocalPortfolioTask(
        **create_spoke_local_portfolio_task_params
    )
    tasks_to_run.append(create_spoke_local_portfolio_task)

    create_spoke_local_portfolio_task_as_dependency_params = {
        'account_id': account_id,
        'region': region,
        'portfolio': launch_details.get('portfolio'),
    }

    create_associations_task_params = {
        'associations': launch_details.get('associations'),
        'puppet_account_id': puppet_account_id,
        'should_use_sns': should_use_sns,
    }
    create_associations_for_portfolio_task = luigi_tasks_and_targets.CreateAssociationsForPortfolioTask(
        **create_spoke_local_portfolio_task_as_dependency_params,
        **create_associations_task_params,
        dependencies=dependencies,
    )
    tasks_to_run.append(create_associations_for_portfolio_task)

    import_into_spoke_local_portfolio_task_params = {
        'hub_portfolio_id': hub_portfolio.get('Id')
    }
    import_into_spoke_local_portfolio_task = luigi_tasks_and_targets.ImportIntoSpokeLocalPortfolioTask(
        **create_spoke_local_portfolio_task_as_dependency_params,
        **import_into_spoke_local_portfolio_task_params,
    )
    tasks_to_run.append(import_into_spoke_local_portfolio_task)

    launch_constraints = launch_details.get('constraints', {}).get('launch', [])
    if len(launch_constraints) > 0:
        create_launch_role_constraints_for_portfolio_task_params = {
            'launch_constraints': launch_constraints,
            'puppet_account_id': puppet_account_id,
            'should_use_sns': should_use_sns,
        }
        create_launch_role_constraints_for_portfolio = luigi_tasks_and_targets.CreateLaunchRoleConstraintsForPortfolio(
            **create_spoke_local_portfolio_task_as_dependency_params,
            **import_into_spoke_local_portfolio_task_params,
            **create_launch_role_constraints_for_portfolio_task_params,
            dependencies=dependencies,
        )
        tasks_to_run.append(create_launch_role_constraints_for_portfolio)
    return tasks_to_run


def convert_manifest_into_task_defs_for_spoke_local_portfolios(manifest, puppet_account_id, should_use_sns, launch_tasks):
    tasks = []
    accounts = manifest.get('accounts', [])
    for launch_name, launch_details in manifest.get('spoke-local-portfolios', {}).items():
        task_def = {
            'launch_tasks': launch_tasks,
            'launch_details': launch_details,
            'puppet_account_id': puppet_account_id,
            'should_use_sns': should_use_sns,
        }

        if manifest.get('configuration'):
            if manifest.get('configuration').get('retry_count'):
                task_def['retry_count'] = manifest.get('configuration').get('retry_count')
        if launch_details.get('configuration'):
            if launch_details.get('configuration').get('retry_count'):
                task_def['retry_count'] = launch_details.get('configuration').get('retry_count')
            if launch_details.get('configuration').get('requested_priority'):
                task_def['requested_priority'] = int(launch_details.get('configuration').get('requested_priority'))

        deploy_to = launch_details .get('deploy_to')
        for tag_list_item in deploy_to.get('tags', []):
            for account in accounts:
                for tag in account.get('tags', []):
                    if tag == tag_list_item.get('tag'):
                        tag_account_def = deepcopy(task_def)
                        tag_account_def['account_id'] = account.get('account_id')

                        regions = tag_list_item.get('regions')
                        if isinstance(regions, str):
                            if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                                for region_enabled in account.get('regions_enabled'):
                                    region_tag_account_def = deepcopy(tag_account_def)
                                    region_tag_account_def['region'] = region_enabled
                                    tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                        **region_tag_account_def
                                    )
                            elif regions == 'default_region':
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = account.get('default_region')
                                tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                    **region_tag_account_def
                                )
                            elif regions == "all":
                                all_regions = cli_command_helpers.get_regions()
                                for region_enabled in all_regions:
                                    region_tag_account_def = deepcopy(tag_account_def)
                                    region_tag_account_def['region'] = region_enabled
                                    tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                        **region_tag_account_def
                                    )
                            else:
                                raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")
                        elif isinstance(regions, list):
                            for region in regions:
                                region_tag_account_def = deepcopy(tag_account_def)
                                region_tag_account_def['region'] = region
                                tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                    **region_tag_account_def
                                )
                        else:
                            raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

        for account_list_item in deploy_to.get('accounts', []):
            for account in accounts:
                if account.get('account_id') == account_list_item.get('account_id'):
                    account_account_def = deepcopy(task_def)
                    account_account_def['account_id'] = account.get('account_id')
                    # account_account_def['account_parameters'] = account.get('parameters', {})

                    regions = account_list_item.get('regions')
                    if isinstance(regions, str):
                        if regions in ["enabled", "regions_enabled", "enabled_regions"]:
                            for region_enabled in account.get('regions_enabled'):
                                region_account_account_def = deepcopy(account_account_def)
                                region_account_account_def['region'] = region_enabled
                                tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                    **region_account_account_def
                                )
                        elif regions == 'default_region':
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = account.get('default_region')
                            tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                **region_account_account_def
                            )
                        elif regions == "all":
                            all_regions = cli_command_helpers.get_regions()
                            for region_enabled in all_regions:
                                region_account_account_def = deepcopy(account_account_def)
                                region_account_account_def['region'] = region_enabled
                                tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                    **region_account_account_def
                                )
                        else:
                            raise Exception(f"Unsupported regions {regions} setting for launch: {launch_name}")

                    elif isinstance(regions, list):
                        for region in regions:
                            region_account_account_def = deepcopy(account_account_def)
                            region_account_account_def['region'] = region
                            tasks += convert_manifest_into_task_defs_for_spoke_local_portfolios_in(
                                **region_account_account_def
                            )
                    else:
                        raise Exception(f"Unexpected regions of {regions} set for launch {launch_name}")

    return tasks
