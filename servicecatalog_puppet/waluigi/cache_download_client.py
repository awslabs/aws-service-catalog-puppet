#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import functools

from betterboto import client as betterboto_client

from servicecatalog_puppet import config


@functools.lru_cache(maxsize=10)
def get_cache_download_client():
    return betterboto_client.CrossAccountClientContextManager(
        "s3",
        config.get_cache_download_role_arn(config.get_executor_account_id()),
        "s3-client",
    )
