#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.general import delete_cloud_formation_stack_task
from servicecatalog_puppet.workflow.generate import ensure_event_bridge_event_bus_task
from servicecatalog_puppet.workflow.generate import generate_policies_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.portfolio.sharing_management import (
    create_share_for_account_launch_region_task,
)


class GenerateSharesTask(tasks.PuppetTask, manifest_mixin.ManifestMixen):
    puppet_account_id = luigi.Parameter()
    manifest_file_path = luigi.Parameter()
    section = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "section": self.section,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = dict(
            deletes=list(), ensure_event_buses=list(), generate_policies=list(),
        )
        for region_name, accounts in self.manifest.get_accounts_by_region().items():
            requirements["deletes"].append(
                delete_cloud_formation_stack_task.DeleteCloudFormationStackTask(
                    account_id=self.puppet_account_id,
                    region=region_name,
                    stack_name="servicecatalog-puppet-shares",
                    nonce=self.cache_invalidator,
                )
            )

        for (
            region_name,
            sharing_policies,
        ) in self.manifest.get_sharing_policies_by_region().items():
            requirements["ensure_event_buses"].append(
                ensure_event_bridge_event_bus_task.EnsureEventBridgeEventBusTask(
                    puppet_account_id=self.puppet_account_id, region=region_name,
                )
            )

            requirements["generate_policies"].append(
                generate_policies_task.GeneratePolicies(
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                    region=region_name,
                    sharing_policies=sharing_policies,
                )
            )

        return requirements

    def run(self):
        tasks = list()
        for (
            region_name,
            shares_by_portfolio_account,
        ) in self.manifest.get_shares_by_region_portfolio_account(
            self.puppet_account_id, self.section
        ).items():
            for (
                portfolio_name,
                shares_by_account,
            ) in shares_by_portfolio_account.items():
                for account_id, share in shares_by_account.items():

                    tasks.append(
                        create_share_for_account_launch_region_task.CreateShareForAccountLaunchRegion(
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            account_id=account_id,
                            region=region_name,
                            portfolio=portfolio_name,
                            sharing_mode=share.get(self.section).get(
                                "sharing_mode",
                                config.get_global_sharing_mode_default(
                                    self.puppet_account_id
                                ),
                            ),
                        )
                    )

        yield tasks
        self.write_output(self.params_for_results_display())
