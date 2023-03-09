#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os

from betterboto import client as betterboto_client
from botocore.config import Config

from servicecatalog_puppet import config, constants


class ClientMixin:
    def is_running_in_spoke(self):
        return self.execution_mode == constants.EXECUTION_MODE_SPOKE

    def spoke_client(self, service):
        kwargs = dict()
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")
        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{config.get_puppet_role_name()}",
            **kwargs,
        )

    def cross_account_client(self, account_id, service, region_name=None):
        region = region_name or self.region
        kwargs = dict(region_name=region)
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")

        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(account_id),
            f"{account_id}-{region}-{config.get_puppet_role_name()}",
            **kwargs,
        )

    def spoke_regional_client(self, service, region_name=None, retry_max_attempts=None):
        region = region_name or self.region
        kwargs = dict(region_name=region)
        if retry_max_attempts is not None:
            kwargs["config"] = Config(retries={"max_attempts": retry_max_attempts,})
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")

        return betterboto_client.CrossAccountClientContextManager(
            service,
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{region}-{config.get_puppet_role_name()}",
            **kwargs,
        )

    def hub_client(self, service):
        kwargs = dict()
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")
        if self.is_running_in_spoke():
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.executor_account_id),
                f"{self.executor_account_id}-{config.get_puppet_role_name()}",
                **kwargs,
            )
        else:
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.puppet_account_id),
                f"{self.puppet_account_id}-{config.get_puppet_role_name()}",
                **kwargs,
            )

    def hub_regional_client(self, service, region_name=None):
        region = region_name or self.region
        kwargs = dict(region_name=region)
        if os.environ.get(f"CUSTOM_ENDPOINT_{service}"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_{service}")

        if self.is_running_in_spoke():
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.executor_account_id),
                f"{self.executor_account_id}-{config.get_puppet_role_name()}",
                **kwargs,
            )
        else:
            return betterboto_client.CrossAccountClientContextManager(
                service,
                config.get_puppet_role_arn(self.puppet_account_id),
                f"{self.puppet_account_id}-{region}-{config.get_puppet_role_name()}",
                **kwargs,
            )

    def organizations_policy_client(self):
        kwargs = dict()
        if os.environ.get(f"CUSTOM_ENDPOINT_organizations"):
            kwargs["endpoint_url"] = os.environ.get(f"CUSTOM_ENDPOINT_organizations")
        if self.is_running_in_spoke():
            raise Exception("Cannot use organizations client in spoke execution")
        else:
            return betterboto_client.CrossAccountClientContextManager(
                "organizations",
                config.get_org_scp_role_arn(self.puppet_account_id),
                "org_scp_role_arn",
            )
