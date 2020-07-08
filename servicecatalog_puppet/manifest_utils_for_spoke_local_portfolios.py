from servicecatalog_puppet import constants

from servicecatalog_puppet.manifest_utils import get_configuration_overrides

import logging

logger = logging.getLogger(__file__)


def get_configuration_from_spoke_local_portfolio(
    manifest, spoke_local_portfolio_details, spoke_local_portfolio_name
):
    configuration = {
        "spoke_local_portfolio_name": spoke_local_portfolio_name,
        "status": spoke_local_portfolio_details.get("status", "shared"),
        "portfolio": spoke_local_portfolio_details.get("portfolio"),
        "associations": spoke_local_portfolio_details.get("associations", []),
        "constraints": spoke_local_portfolio_details.get("constraints", {}),
        "depends_on": spoke_local_portfolio_details.get("depends_on", []),
        "retry_count": spoke_local_portfolio_details.get("retry_count", 1),
        "requested_priority": spoke_local_portfolio_details.get(
            "requested_priority", 0
        ),
        "worker_timeout": spoke_local_portfolio_details.get(
            "timeoutInSeconds", constants.DEFAULT_TIMEOUT
        ),
        "product_generation_method": spoke_local_portfolio_details.get(
            "product_generation_method", "copy"
        ),
    }
    configuration.update(
        get_configuration_overrides(manifest, spoke_local_portfolio_details)
    )
    return configuration
