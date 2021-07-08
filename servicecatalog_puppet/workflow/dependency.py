from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generate import generate_shares_task


def generate_dependency_tasks(
    dependencies,
    manifest_file_path,
    puppet_account_id,
    account_id,
    region,
    execution_mode,
):
    is_running_in_hub = execution_mode != constants.EXECUTION_MODE_SPOKE

    from servicecatalog_puppet.workflow.launch import (
        launch_task,
        launch_for_account_task,
        launch_for_region_task,
        launch_for_account_and_region_task,
    )
    from servicecatalog_puppet.workflow.stack import (
        stack_task,
        stack_for_account_task,
        stack_for_region_task,
        stack_for_account_and_region_task,
    )
    from servicecatalog_puppet.workflow.spoke_local_portfolios import (
        spoke_local_portfolio_task,
        spoke_local_portfolio_for_account_task,
        spoke_local_portfolio_for_region_task,
        spoke_local_portfolio_for_account_and_region_task,
    )
    from servicecatalog_puppet.workflow.assertions import (
        assertion_task,
        assertion_for_account_task,
        assertion_for_region_task,
        assertion_for_account_and_region_task,
    )
    from servicecatalog_puppet.workflow.codebuild_runs import (
        code_build_run_task,
        code_build_run_for_account_task,
        code_build_run_for_region_task,
        code_build_run_for_account_and_region_task,
    )
    from servicecatalog_puppet.workflow.lambda_invocations import (
        lambda_invocation_task,
        lambda_invocation_for_account_task,
        lambda_invocation_for_region_task,
        lambda_invocation_for_account_and_region_task,
    )

    these_dependencies = list()
    common_args = dict(
        manifest_file_path=manifest_file_path, puppet_account_id=puppet_account_id,
    )
    for depends_on in dependencies:
        if depends_on.get("type") == constants.LAUNCH:
            if depends_on.get(constants.AFFINITY) == constants.LAUNCH:
                these_dependencies.append(
                    launch_task.LaunchTask(
                        **common_args, launch_name=depends_on.get("name"),
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account":
                these_dependencies.append(
                    launch_for_account_task.LaunchForAccountTask(
                        **common_args,
                        launch_name=depends_on.get("name"),
                        account_id=account_id,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "region":
                these_dependencies.append(
                    launch_for_region_task.LaunchForRegionTask(
                        **common_args,
                        launch_name=depends_on.get("name"),
                        region=region,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account-and-region":
                these_dependencies.append(
                    launch_for_account_and_region_task.LaunchForAccountAndRegionTask(
                        **common_args,
                        launch_name=depends_on.get("name"),
                        account_id=account_id,
                        region=region,
                    )
                )

        elif depends_on.get("type") == constants.STACK:
            if depends_on.get(constants.AFFINITY) == constants.STACK:
                these_dependencies.append(
                    stack_task.StackTask(
                        **common_args, stack_name=depends_on.get("name"),
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account":
                these_dependencies.append(
                    stack_for_account_task.StackForAccountTask(
                        **common_args,
                        stack_name=depends_on.get("name"),
                        account_id=account_id,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "region":
                these_dependencies.append(
                    stack_for_region_task.StackForRegionTask(
                        **common_args, stack_name=depends_on.get("name"), region=region,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account-and-region":
                these_dependencies.append(
                    stack_for_account_and_region_task.StackForAccountAndRegionTask(
                        **common_args,
                        stack_name=depends_on.get("name"),
                        account_id=account_id,
                        region=region,
                    )
                )

        elif (
            is_running_in_hub
            and depends_on.get("type") == constants.SPOKE_LOCAL_PORTFOLIO
        ):
            if depends_on.get(constants.AFFINITY) == constants.SPOKE_LOCAL_PORTFOLIO:
                these_dependencies.append(
                    spoke_local_portfolio_task.SpokeLocalPortfolioTask(
                        **common_args,
                        spoke_local_portfolio_name=depends_on.get("name"),
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account":
                these_dependencies.append(
                    spoke_local_portfolio_for_account_task.SpokeLocalPortfolioForAccountTask(
                        **common_args,
                        spoke_local_portfolio_name=depends_on.get("name"),
                        account_id=account_id,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "region":
                these_dependencies.append(
                    spoke_local_portfolio_for_region_task.SpokeLocalPortfolioForRegionTask(
                        **common_args,
                        spoke_local_portfolio_name=depends_on.get("name"),
                        region=region,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account-and-region":
                these_dependencies.append(
                    spoke_local_portfolio_for_account_and_region_task.SpokeLocalPortfolioForAccountAndRegionTask(
                        **common_args,
                        spoke_local_portfolio_name=depends_on.get("name"),
                        account_id=account_id,
                        region=region,
                    )
                )
        elif is_running_in_hub and depends_on.get("type") == constants.ASSERTION:
            if depends_on.get(constants.AFFINITY) == constants.ASSERTION:
                these_dependencies.append(
                    assertion_task.AssertionTask(
                        **common_args, assertion_name=depends_on.get("name"),
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account":
                these_dependencies.append(
                    assertion_for_account_task.AssertionForAccountTask(
                        **common_args,
                        assertion_name=depends_on.get("name"),
                        account_id=account_id,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "region":
                these_dependencies.append(
                    assertion_for_region_task.AssertionForRegionTask(
                        **common_args,
                        assertion_name=depends_on.get("name"),
                        region=region,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account-and-region":
                these_dependencies.append(
                    assertion_for_account_and_region_task.AssertionForAccountAndRegionTask(
                        **common_args,
                        assertion_name=depends_on.get("name"),
                        account_id=account_id,
                        region=region,
                    )
                )

        elif is_running_in_hub and depends_on.get("type") == constants.CODE_BUILD_RUN:
            if depends_on.get(constants.AFFINITY) == constants.CODE_BUILD_RUN:
                these_dependencies.append(
                    code_build_run_task.CodeBuildRunTask(
                        **common_args, code_build_run_name=depends_on.get("name"),
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account":
                these_dependencies.append(
                    code_build_run_for_account_task.CodeBuildRunForAccountTask(
                        **common_args,
                        code_build_run_name=depends_on.get("name"),
                        account_id=account_id,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "region":
                these_dependencies.append(
                    code_build_run_for_region_task.CodeBuildRunForRegionTask(
                        **common_args,
                        code_build_run_name=depends_on.get("name"),
                        region=region,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account-and-region":
                these_dependencies.append(
                    code_build_run_for_account_and_region_task.CodeBuildRunForAccountAndRegionTask(
                        **common_args,
                        code_build_run_name=depends_on.get("name"),
                        account_id=account_id,
                        region=region,
                    )
                )

        elif (
            is_running_in_hub and depends_on.get("type") == constants.LAMBDA_INVOCATION
        ):
            if depends_on.get(constants.AFFINITY) == constants.LAMBDA_INVOCATION:
                these_dependencies.append(
                    lambda_invocation_task.LambdaInvocationTask(
                        **common_args, lambda_invocation_name=depends_on.get("name"),
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account":
                these_dependencies.append(
                    lambda_invocation_for_account_task.LambdaInvocationForAccountTask(
                        **common_args,
                        lambda_invocation_name=depends_on.get("name"),
                        account_id=account_id,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "region":
                these_dependencies.append(
                    lambda_invocation_for_region_task.LambdaInvocationForRegionTask(
                        **common_args,
                        lambda_invocation_name=depends_on.get("name"),
                        region=region,
                    )
                )
            if depends_on.get(constants.AFFINITY) == "account-and-region":
                these_dependencies.append(
                    lambda_invocation_for_account_and_region_task.LambdaInvocationForAccountAndRegionTask(
                        **common_args,
                        lambda_invocation_name=depends_on.get("name"),
                        account_id=account_id,
                        region=region,
                    )
                )
    return these_dependencies


class DependenciesMixin(object):
    def get_section_dependencies(self):
        dependencies = (
            self.manifest.get(self.section_name)
            .get(self.item_name)
            .get("depends_on", [])
        )

        should_generate_shares = not (
            self.execution_mode == constants.EXECUTION_MODE_SPOKE or self.is_dry_run
        )

        these_dependencies = generate_dependency_tasks(
            dependencies,
            self.manifest_file_path,
            self.puppet_account_id,
            self.account_id,
            self.region,
            self.execution_mode,
        )

        if self.section_name in [constants.SPOKE_LOCAL_PORTFOLIOS, constants.LAUNCHES]:
            if should_generate_shares:
                these_dependencies.append(
                    generate_shares_task.GenerateSharesTask(
                        puppet_account_id=self.puppet_account_id,
                        manifest_file_path=self.manifest_file_path,
                        section=self.section_name,
                    )
                )

        return these_dependencies
