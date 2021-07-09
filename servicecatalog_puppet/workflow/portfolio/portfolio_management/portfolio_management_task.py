import luigi

from servicecatalog_puppet.workflow import tasks


class PortfolioManagementTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()
