from servicecatalog_puppet import constants
from servicecatalog_puppet.manifest_utils import get_configuration_overrides
from servicecatalog_puppet.workflow import provisioning

import logging

logger = logging.getLogger(__file__)


def get_configuration_from_launch(manifest, launch_name):
    launch_details = manifest.get("launches").get(launch_name)
    configuration = {
        "status": launch_details.get("status", constants.PROVISIONED),
        "launch_name": launch_name,
        "portfolio": launch_details.get("portfolio"),
        "product": launch_details.get("product"),
        "version": launch_details.get("version"),
        "parameters": [],
        "ssm_param_inputs": [],
        "launch_parameters": launch_details.get("parameters", {}),
        "manifest_parameters": manifest.get("parameters", {}),
        "depends_on": launch_details.get("depends_on", []),
        "ssm_param_outputs": launch_details.get("outputs", {}).get("ssm", []),
        "retry_count": launch_details.get("retry_count", 1),
        "requested_priority": launch_details.get("requested_priority", 0),
        "worker_timeout": launch_details.get(
            "timeoutInSeconds", constants.DEFAULT_TIMEOUT
        ),
    }
    configuration.update(get_configuration_overrides(manifest, launch_details))
    return configuration


# TODO - delete?
def generate_launch_tasks(
    manifest,
    puppet_account_id,
    should_use_sns,
    should_use_product_plans,
    include_expanded_from=False,
    single_account=None,
    is_dry_run=False,
    execution_mode="hub",
):
    logger.info(f"m.generate_launch_tasks execution_mode is {execution_mode}")
    logger.info(f"execution_mode {execution_mode}")
    if execution_mode == constants.EXECUTION_MODE_SPOKE:
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
                execution_mode=execution_mode,
            )
            for launch_name, launch_details in manifest.get("launches", {}).items()
            if launch_details.get("execution") == constants.EXECUTION_MODE_SPOKE
        ]
    else:
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
                execution_mode=execution_mode,
            )
            for launch_name, launch_details in manifest.get("launches", {}).items()
            if launch_details.get("execution") != constants.EXECUTION_MODE_SPOKE
        ]
