#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import logging

from servicecatalog_puppet import constants
from servicecatalog_puppet.manifest_utils import get_configuration_overrides

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
