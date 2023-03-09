#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os

from servicecatalog_puppet import (
    constants,
    environmental_variables,
    serialisation_utils,
)


class EnvVarMixin:
    @property
    def drift_token(self):
        return os.environ.get(environmental_variables.DRIFT_TOKEN, "NOW")

    @property
    def run_token(self):
        return os.environ.get(environmental_variables.RUN_TOKEN, "NOW")

    @property
    def should_use_product_plans(self):
        if self.execution_mode == constants.EXECUTION_MODE_HUB:
            return (
                os.environ.get(environmental_variables.SHOULD_USE_PRODUCT_PLANS, "True")
                == "True"
            )
        else:
            return False

    @property
    def single_account(self):
        return os.environ.get("SCT_SINGLE_ACCOUNT", "None")

    @property
    def should_delete_rollback_complete_stacks(self):
        return (
            str(
                os.environ.get(
                    environmental_variables.SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS,
                    constants.CONFIG_SHOULD_DELETE_ROLLBACK_COMPLETE_STACKS_DEFAULT,
                )
            ).upper()
            == "TRUE"
        )

    @property
    def initialiser_stack_tags(self):
        initialiser_stack_tags_value = os.environ.get(
            environmental_variables.INITIALISER_STACK_TAGS, None
        )
        if initialiser_stack_tags_value is None:
            raise Exception(
                f"You must export {environmental_variables.INITIALISER_STACK_TAGS}"
            )
        return serialisation_utils.json_loads(initialiser_stack_tags_value)

    @property
    def spoke_execution_mode_deploy_env(self):
        return os.environ.get(
            environmental_variables.SPOKE_EXECUTION_MODE_DEPLOY_ENV,
            constants.SPOKE_EXECUTION_MODE_DEPLOY_ENV_DEFAULT,
        )

    @property
    def should_use_sns(self):
        return os.environ.get(environmental_variables.SHOULD_USE_SNS, "False") == "True"

    @property
    def is_dry_run(self):
        return os.environ.get("SCT_IS_DRY_RUN", "False") == "True"

    @property
    def executor_account_id(self):
        return os.environ.get(environmental_variables.EXECUTOR_ACCOUNT_ID)

    @property
    def execution_mode(self):
        return os.environ.get(
            environmental_variables.EXECUTION_MODE, constants.EXECUTION_MODE_HUB
        )
