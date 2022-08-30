#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0


import json
import os

import luigi

from servicecatalog_puppet import environmental_variables


class environmentalParams(luigi.Config):
    home_region = luigi.Parameter(
        default=os.environ.get(environmental_variables.HOME_REGION)
    )
    regions = luigi.Parameter(
        default=json.loads(os.environ.get(environmental_variables.REGIONS, ""))
    )

    should_collect_cloudformation_events = luigi.Parameter(
        default=os.environ.get(environmental_variables.SHOULD_USE_SNS)
    )
    should_forward_events_to_eventbridge = luigi.Parameter(
        default=os.environ.get(
            environmental_variables.SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE
        )
    )
    should_forward_failures_to_opscenter = luigi.Parameter(
        default=os.environ.get(
            environmental_variables.SHOULD_FORWARD_FAILURES_TO_OPSCENTER
        )
    )
    version = luigi.Parameter(default=os.environ.get(environmental_variables.VERSION))
