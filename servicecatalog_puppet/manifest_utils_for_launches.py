from servicecatalog_puppet import constants
from servicecatalog_puppet.manifest_utils import get_configuration_overrides, get_actions_from, get_task_defs_from_details
from servicecatalog_puppet.workflow import provisioning

import logging

logger = logging.getLogger(__file__)


def get_configuration_from_launch(manifest, launch_details, launch_name):
    configuration = {
        'status': launch_details.get('status', constants.PROVISIONED),

        'launch_name': launch_name,
        'portfolio': launch_details.get('portfolio'),
        'product': launch_details.get('product'),
        'version': launch_details.get('version'),

        'parameters': [],
        'ssm_param_inputs': [],
        'launch_parameters': launch_details.get('parameters', {}),
        'manifest_parameters': manifest.get('parameters', {}),

        'depends_on': launch_details.get('depends_on', []),

        'ssm_param_outputs': launch_details.get('outputs', {}).get('ssm', []),

        'retry_count': launch_details.get('retry_count', 1),
        'requested_priority': launch_details.get('requested_priority', 0),
        'worker_timeout': launch_details.get('timeoutInSeconds', constants.DEFAULT_TIMEOUT),
    }
    configuration.update(
        get_configuration_overrides(manifest, launch_details)
    )
    return configuration


def generate_launch_task_defs_for_launch(
        launch_name, manifest, puppet_account_id, should_use_sns, should_use_product_plans, include_expanded_from=False,
        single_account=None, is_dry_run=False,
):
    accounts = manifest.get('accounts', [])
    actions = manifest.get('actions', {})

    launch_details = manifest.get('launches').get(launch_name)

    configuration = get_configuration_from_launch(manifest, launch_details, launch_name)
    configuration['single_account'] = single_account
    configuration['is_dry_run'] = is_dry_run
    configuration['puppet_account_id'] = puppet_account_id
    configuration['should_use_sns'] = should_use_sns
    configuration['should_use_product_plans'] = should_use_product_plans
    return {
        'pre_actions': get_actions_from(launch_name, launch_details, 'pre', actions, 'launch'),
        'post_actions': get_actions_from(launch_name, launch_details, 'post', actions, 'launch'),
        'task_defs': get_task_defs_from_details(
            launch_details, accounts, include_expanded_from, launch_name, configuration
        )
    }


def generate_launch_tasks(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans, include_expanded_from=False,
        single_account=None, is_dry_run=False
):
    return [
        provisioning.LaunchTask(
            launch_name=launch_name,
            manifest=manifest,
            puppet_account_id=puppet_account_id,
            should_use_sns=should_use_sns,
            should_use_product_plans=should_use_product_plans,
            include_expanded_from=include_expanded_from,
            single_account=single_account,
            is_dry_run=is_dry_run,
        ) for launch_name in manifest.get('launches', {}).keys()
    ]
