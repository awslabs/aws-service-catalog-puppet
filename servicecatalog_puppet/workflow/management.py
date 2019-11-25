import luigi

import sdk
from . import tasks


class BootstrapSpokeAsTask(tasks.PuppetTask):
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()
    iam_role_arns = luigi.ListParameter()
    role_name = luigi.Parameter()

    @property
    def uid(self):
        return self.account_id

    def output(self):
        return luigi.LocalTarget(
            f"output/{self.__class__.__name__}/"
            f"{self.uid}.json"
        )

    @property
    def resources(self):
        return {}

    def params_for_results_display(self):
        return {
            "launch_name": 'na',
            "account_id": self.account_id,
        }

    def run(self):
        iam_role_arns_to_use = [iam_role_arn for iam_role_arn in self.iam_role_arns]
        iam_role_arns_to_use.append(
            f"arn:aws:iam::{self.account_id}:role/{self.role_name}"
        )
        sdk.bootstrap_spoke_as(
            self.puppet_account_id,
            iam_role_arns_to_use,
        )
        self.write_output({})
