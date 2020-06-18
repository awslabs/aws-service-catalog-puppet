import luigi
from servicecatalog_puppet import manifest_utils, manifest_utils_for_launches

from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow import provisioning as provisioning_tasks


class ManifestTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def run(self):
        with open(self.manifest_file_path, 'r') as m:
            manifest = manifest_utils.load(m, self.puppet_account_id)
        self.write_output(manifest)


class SectionTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()
    execution_mode = luigi.Parameter()

    def requires(self):
        return {
            'manifest': ManifestTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
            )
        }


# class SpokeLocalPortfolioSectionTask(SectionTask):
#     def run(self):
#         manifest = manifest_utils.load(self.manifest_file_path, self.puppet_account_id)
#         if not is_dry_run:
#             logger.info("Generating sharing tasks")
#             spoke_local_portfolios_tasks = manifest_utils_for_spoke_local_portfolios.generate_spoke_local_portfolios_tasks(
#                 manifest,
#                 puppet_account_id,
#                 should_use_sns,
#                 should_use_product_plans,
#                 include_expanded_from=False,
#                 single_account=single_account,
#                 is_dry_run=is_dry_run,
#             )
#             tasks_to_run += spoke_local_portfolios_tasks
#             logger.info("Finished generating sharing tasks")
#
#         logger.info("Finished generating all tasks")
#         return tasks_to_run