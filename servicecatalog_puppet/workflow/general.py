import luigi
from betterboto import client as betterboto_client

from servicecatalog_puppet.workflow import tasks


class DeleteCloudFormationStackTask(tasks.PuppetTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
    stack_name = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "account_id": self.account_id,
            "region": self.region,
            "stack_name": self.stack_name,
        }

    def api_calls_used(self):
        return {
            f"cloudformation.describe_stacks_single_page_{self.account_id}_{self.region}": 1,
            f"cloudformation.delete_stack_{self.account_id}_{self.region}": 1,
            f"cloudformation.describe_stack_events_{self.account_id}_{self.region}": 1,
        }

    def run(self):
        self.info("Starting")
        with betterboto_client.CrossAccountClientContextManager(
            "cloudformation",
            f"arn:aws:iam::{self.account_id}:role/servicecatalog-puppet/PuppetRole",
            f"{self.account_id}-{self.region}-PuppetRole",
            region_name=self.region,
        ) as cloudformation:
            self.info(f"About to delete the stack: {self.stack_name}")
            cloudformation.ensure_deleted(StackName=self.stack_name)
        self.write_output(self.params_for_results_display())
        self.info("Finished")
