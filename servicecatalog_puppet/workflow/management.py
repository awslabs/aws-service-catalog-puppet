#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import config, sdk, serialisation_utils
from servicecatalog_puppet.workflow import tasks


class BootstrapSpokeAsTask(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    iam_role_arns = luigi.ListParameter()
    role_name = luigi.Parameter()
    permission_boundary = luigi.Parameter()
    puppet_role_name = luigi.Parameter()
    puppet_role_path = luigi.Parameter()
    tag = luigi.ListParameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
        }

    def run(self):
        partition = config.get_partition()
        iam_role_arns_to_use = [iam_role_arn for iam_role_arn in self.iam_role_arns]
        iam_role_arns_to_use.append(
            f"arn:{partition}:iam::{self.account_id}:role/{self.role_name}"
        )
        sdk.bootstrap_spoke_as(
            self.puppet_account_id,
            iam_role_arns_to_use,
            self.permission_boundary,
            self.puppet_role_name,
            self.puppet_role_path,
            self.tag,
        )
        self.write_output(self.params_for_results_display())

    def write_output(self, content):
        with self.output().open("w") as f:
            content_to_write = serialisation_utils.json_dumps(content).decode("utf-8")
            f.write(content_to_write)

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.__class__.__name__}/{self.puppet_account_id}/{self.account_id}.json",
        )
