import luigi

from servicecatalog_puppet.workflow.launch import launch_for_task

from servicecatalog_puppet.workflow.generic import generic_for_account_and_region_task


class LaunchForAccountAndRegionTask(
    generic_for_account_and_region_task.GenericForAccountAndRegionTask,
    launch_for_task.LaunchForTask,
):
    account_id = luigi.Parameter()
    region = luigi.Parameter()
