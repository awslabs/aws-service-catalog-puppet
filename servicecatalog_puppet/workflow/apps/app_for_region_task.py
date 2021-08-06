import luigi

from servicecatalog_puppet.workflow.apps import app_for_task
from servicecatalog_puppet.workflow.generic import generic_for_region_task


class AppForRegionTask(
    generic_for_region_task.GenericForRegionTask, app_for_task.AppForTask
):
    region = luigi.Parameter()
