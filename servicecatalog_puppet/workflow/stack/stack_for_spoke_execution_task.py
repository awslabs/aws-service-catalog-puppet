import functools

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.assertions import assertion_task
from servicecatalog_puppet.workflow.codebuild_runs import code_build_run_task
from servicecatalog_puppet.workflow.lambda_invocations import lambda_invocation_task
from servicecatalog_puppet.workflow.stack import stack_task
from servicecatalog_puppet.workflow.stack import provisioning_task
from servicecatalog_puppet.workflow.launch import run_deploy_in_spoke_task
from servicecatalog_puppet.workflow.spoke_local_portfolios import (
    spoke_local_portfolio_task,
)


class StackForSpokeExecutionTask(
    provisioning_task.ProvisioningTask, dependency.DependenciesMixin
):
    stack_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "stack_name": self.stack_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):

        these_dependencies = list()
        common_args = dict(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
        )
        dependencies = self.manifest.get_stack(self.stack_name).get("depends_on", [])
        for depends_on in dependencies:
            depends_on_affinity = depends_on.get(constants.AFFINITY)
            depends_on_type = depends_on.get("type")
            if depends_on_type == constants.STACK:
                if depends_on_affinity == constants.STACK:
                    dep = self.manifest.get_stack(depends_on.get("name"))
                    if dep.get("execution") == constants.EXECUTION_MODE_SPOKE:
                        these_dependencies.append(
                            StackForSpokeExecutionTask(
                                **common_args, stack_name=depends_on.get("name"),
                            )
                        )
                    else:
                        these_dependencies.append(
                            stack_task.StackTask(
                                **common_args, stack_name=depends_on.get("name"),
                            )
                        )
                else:
                    raise Exception(
                        "Could can only depend on a stack using affinity stack when using spoke execution mode"
                    )

            elif depends_on_type == constants.SPOKE_LOCAL_PORTFOLIO:
                if depends_on_affinity == constants.SPOKE_LOCAL_PORTFOLIO:
                    these_dependencies.append(
                        spoke_local_portfolio_task.SpokeLocalPortfolioTask(
                            **common_args,
                            spoke_local_portfolio_name=depends_on.get("name"),
                        )
                    )
                else:
                    raise Exception(
                        "Could can only depend on a spoke_local_portfolio using affinity spoke_local_portfolios when using spoke execution mode"
                    )

            elif depends_on_type == constants.ASSERTION:
                if depends_on_affinity == constants.ASSERTION:
                    these_dependencies.append(
                        assertion_task.AssertionTask(
                            **common_args, assertion_name=depends_on.get("name"),
                        )
                    )
                else:
                    raise Exception(
                        "Could can only depend on an assertion using affinity assertion when using spoke execution mode"
                    )

            elif depends_on_type == constants.CODE_BUILD_RUN:
                if depends_on_affinity == constants.CODE_BUILD_RUN:
                    these_dependencies.append(
                        code_build_run_task.CodeBuildRunTask(
                            **common_args, code_build_run_name=depends_on.get("name"),
                        )
                    )
                else:
                    raise Exception(
                        "Could can only depend on a code_build_run using affinity code_build_run when using spoke execution mode"
                    )

            elif depends_on_type == constants.LAMBDA_INVOCATION:
                if depends_on_affinity == constants.LAMBDA_INVOCATION:
                    these_dependencies.append(
                        lambda_invocation_task.LambdaInvocationTask(
                            **common_args,
                            lambda_invocation_name=depends_on.get("name"),
                        )
                    )
                else:
                    raise Exception(
                        "Could can only depend on a lambda_invocation using affinity lambda_invocation when using spoke execution mode"
                    )

        return these_dependencies

    @functools.lru_cache(maxsize=8)
    def get_tasks(self):
        tasks_to_run = list()
        for account_id in self.manifest.get_account_ids_used_for_section_item(
            self.puppet_account_id, self.section_name, self.stack_name
        ):
            tasks_to_run.append(
                run_deploy_in_spoke_task.RunDeployInSpokeTask(
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                    account_id=account_id,
                )
            )
        return tasks_to_run

    def run(self):
        tasks_to_run = self.get_tasks()
        yield tasks_to_run
        self.write_output(self.params_for_results_display())
