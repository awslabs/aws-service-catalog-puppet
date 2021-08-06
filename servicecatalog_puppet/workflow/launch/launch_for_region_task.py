import luigi

from servicecatalog_puppet.workflow.launch import launch_for_task
from servicecatalog_puppet.workflow.generic import generic_for_region_task


class LaunchForRegionTask(
    generic_for_region_task.GenericForRegionTask, launch_for_task.LaunchForTask
):
    region = luigi.Parameter()
