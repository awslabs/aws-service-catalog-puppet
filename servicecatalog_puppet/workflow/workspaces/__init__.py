#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum


class Limits(Enum):
    """1/number should be rational"""

    CODEBUILD_CONCURRENT_PROJECTS = 5
    SSM_GET_PARAMETER_PER_REGION_OF_ACCOUNT = 5
