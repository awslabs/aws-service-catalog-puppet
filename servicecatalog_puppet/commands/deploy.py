#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import os
from datetime import datetime

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.commands.misc import generate_tasks
from servicecatalog_puppet.workflow import runner as runner
import logging

logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def deploy(
    f,
    puppet_account_id,
    executor_account_id,
    single_account=None,
    num_workers=10,
    is_dry_run=False,
    is_list_launches=False,
    execution_mode="hub",
    on_complete_url=None,
    running_exploded=False,
    output_cache_starting_point="",
):
    if os.environ.get("SCT_CACHE_INVALIDATOR"):
        logger.info(
            f"Found existing SCT_CACHE_INVALIDATOR: {os.environ.get('SCT_CACHE_INVALIDATOR')}"
        )
    else:
        os.environ["SCT_CACHE_INVALIDATOR"] = str(datetime.now())

    os.environ["SCT_EXECUTION_MODE"] = str(execution_mode)
    os.environ["SCT_SINGLE_ACCOUNT"] = str(single_account)
    os.environ["SCT_IS_DRY_RUN"] = str(is_dry_run)
    os.environ["EXECUTOR_ACCOUNT_ID"] = str(executor_account_id)
    os.environ["SCT_SHOULD_USE_SNS"] = str(config.get_should_use_sns(puppet_account_id))
    os.environ["SCT_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS"] = str(
        config.get_should_delete_rollback_complete_stacks(puppet_account_id)
    )
    os.environ["SCT_SHOULD_USE_PRODUCT_PLANS"] = str(
        config.get_should_use_product_plans(
            puppet_account_id, os.environ.get("AWS_DEFAULT_REGION")
        )
    )
    os.environ["SCT_INITIALISER_STACK_TAGS"] = json.dumps(
        config.get_initialiser_stack_tags()
    )
    tasks_to_run = generate_tasks(
        f, puppet_account_id, executor_account_id, execution_mode, is_dry_run
    )
    runner.run_tasks(
        puppet_account_id,
        executor_account_id,
        tasks_to_run,
        num_workers,
        is_dry_run,
        is_list_launches,
        execution_mode,
        on_complete_url,
        running_exploded,
        output_cache_starting_point=output_cache_starting_point,
    )
