from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_base_task
from servicecatalog_puppet.workflow.codebuild_runs import (
    code_build_run_for_account_and_region_task,
)
from servicecatalog_puppet.workflow.codebuild_runs import (
    code_build_run_for_account_task,
)
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_for_region_task
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_task
from servicecatalog_puppet.workflow.manifest import section_task


class CodeBuildRunsSectionTask(
    code_build_run_base_task.CodeBuildRunBaseTask, section_task.SectionTask
):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()

        for name, details in self.manifest.get(constants.CODE_BUILD_RUNS, {}).items():
            requirements += self.handle_requirements_for(
                name,
                constants.CODE_BUILD_RUN,
                constants.CODE_BUILD_RUNS,
                code_build_run_for_region_task.CodeBuildRunForRegionTask,
                code_build_run_for_account_task.CodeBuildRunForAccountTask,
                code_build_run_for_account_and_region_task.CodeBuildRunForAccountAndRegionTask,
                code_build_run_task.CodeBuildRunTask,
                dict(
                    code_build_run_name=name,
                    puppet_account_id=self.puppet_account_id,
                    manifest_file_path=self.manifest_file_path,
                ),
            )

        return requirements

    def run(self):
        self.write_output(self.manifest.get(self.section_name))
