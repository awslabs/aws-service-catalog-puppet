#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks


class GeneratePoliciesTemplate(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    manifest_file_path = luigi.Parameter()
    region = luigi.Parameter()
    sharing_policies = luigi.DictParameter()

    @property
    def output_suffix(self):
        return "template.yaml"

    def params_for_results_display(self):
        return {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def run(self):
        if len(self.sharing_policies.get("accounts")) > 50:
            self.warning(
                "You have specified more than 50 accounts will not create the eventbus policy and spoke execution mode will not work"
            )
        rendered = config.env.get_template("policies.template.yaml.j2").render(
            sharing_policies=self.sharing_policies,
            VERSION=constants.VERSION,
            HOME_REGION=constants.HOME_REGION,
        )
        with self.output().open("w") as output_file:
            output_file.write(rendered)
