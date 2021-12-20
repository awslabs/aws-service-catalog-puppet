#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow.generate import generate_shares_task


def generate_dependency_tasks(
    dependencies,
    manifest_file_path,
    puppet_account_id,
    account_id,
    ou_name,
    region,
    execution_mode,
):
    is_running_in_hub = execution_mode != constants.EXECUTION_MODE_SPOKE

    these_dependencies = list()

    for depends_on in dependencies:
        these_dependencies.append(
            generate_dependency_task(
                depends_on,
                manifest_file_path,
                puppet_account_id,
                account_id,
                ou_name,
                region,
                is_running_in_hub,
            )
        )

    return these_dependencies


def generate_dependency_task(
    depends_on,
    manifest_file_path,
    puppet_account_id,
    account_id,
    ou_name,
    region,
    is_running_in_hub,
):
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
    from servicecatalog_puppet.workflow.simulate_policies import (
        simulate_policy_task,
        simulate_policy_for_account_task,
        simulate_policy_for_region_task,
        simulate_policy_for_account_and_region_task,
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
    from servicecatalog_puppet.workflow.apps import (
        app_task,
        app_for_account_task,
        app_for_region_task,
        app_for_account_and_region_task,
    )
    from servicecatalog_puppet.workflow.workspaces import (
        workspace_task,
        workspace_for_account_task,
        workspace_for_region_task,
        workspace_for_account_and_region_task,
    )
    from servicecatalog_puppet.workflow.service_control_policies import (
        service_control_policies_task,
    )

    common_args = dict(
        manifest_file_path=manifest_file_path, puppet_account_id=puppet_account_id,
    )

    if depends_on.get("type") == constants.LAUNCH:
        if depends_on.get(constants.AFFINITY) == constants.LAUNCH:
            return launch_task.LaunchTask(
                **common_args, launch_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return launch_for_account_task.LaunchForAccountTask(
                **common_args,
                launch_name=depends_on.get("name"),
                account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return launch_for_region_task.LaunchForRegionTask(
                **common_args, launch_name=depends_on.get("name"), region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return launch_for_account_and_region_task.LaunchForAccountAndRegionTask(
                **common_args,
                launch_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )

    elif depends_on.get("type") == constants.STACK:
        if depends_on.get(constants.AFFINITY) == constants.STACK:
            return stack_task.StackTask(
                **common_args, stack_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return stack_for_account_task.StackForAccountTask(
                **common_args, stack_name=depends_on.get("name"), account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return stack_for_region_task.StackForRegionTask(
                **common_args, stack_name=depends_on.get("name"), region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return stack_for_account_and_region_task.StackForAccountAndRegionTask(
                **common_args,
                stack_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )

    elif depends_on.get("type") == constants.APP:
        if depends_on.get(constants.AFFINITY) == constants.APP:
            return app_task.AppTask(**common_args, app_name=depends_on.get("name"),)
        if depends_on.get(constants.AFFINITY) == "account":
            return app_for_account_task.AppForAccountTask(
                **common_args, app_name=depends_on.get("name"), account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return app_for_region_task.AppForRegionTask(
                **common_args, app_name=depends_on.get("name"), region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return app_for_account_and_region_task.AppForAccountAndRegionTask(
                **common_args,
                app_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )

    elif depends_on.get("type") == constants.WORKSPACE:
        if depends_on.get(constants.AFFINITY) == constants.WORKSPACE:
            return workspace_task.WorkspaceTask(
                **common_args, workspace_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return workspace_for_account_task.WorkspaceForAccountTask(
                **common_args,
                workspace_name=depends_on.get("name"),
                account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return workspace_for_region_task.WorkspaceForRegionTask(
                **common_args, workspace_name=depends_on.get("name"), region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return workspace_for_account_and_region_task.WorkspaceForAccountAndRegionTask(
                **common_args,
                workspace_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )

    elif depends_on.get("type") == constants.SERVICE_CONTROL_POLICY:
        if depends_on.get(constants.AFFINITY) == constants.SERVICE_CONTROL_POLICY:
            return service_control_policies_task.ServiceControlPoliciesTask(
                **common_args, service_control_policies_name=depends_on.get("name"),
            )
        else:
            raise Exception(
                f"Affinity of {depends_on.get(constants.AFFINITY)} is not supported for this action"
            )

    elif (
        is_running_in_hub and depends_on.get("type") == constants.SPOKE_LOCAL_PORTFOLIO
    ):
        if depends_on.get(constants.AFFINITY) == constants.SPOKE_LOCAL_PORTFOLIO:
            return spoke_local_portfolio_task.SpokeLocalPortfolioTask(
                **common_args, spoke_local_portfolio_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return spoke_local_portfolio_for_account_task.SpokeLocalPortfolioForAccountTask(
                **common_args,
                spoke_local_portfolio_name=depends_on.get("name"),
                account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return spoke_local_portfolio_for_region_task.SpokeLocalPortfolioForRegionTask(
                **common_args,
                spoke_local_portfolio_name=depends_on.get("name"),
                region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return spoke_local_portfolio_for_account_and_region_task.SpokeLocalPortfolioForAccountAndRegionTask(
                **common_args,
                spoke_local_portfolio_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )
    elif is_running_in_hub and depends_on.get("type") == constants.ASSERTION:
        if depends_on.get(constants.AFFINITY) == constants.ASSERTION:
            return assertion_task.AssertionTask(
                **common_args, assertion_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return assertion_for_account_task.AssertionForAccountTask(
                **common_args,
                assertion_name=depends_on.get("name"),
                account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return assertion_for_region_task.AssertionForRegionTask(
                **common_args, assertion_name=depends_on.get("name"), region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return assertion_for_account_and_region_task.AssertionForAccountAndRegionTask(
                **common_args,
                assertion_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )
    elif is_running_in_hub and depends_on.get("type") == constants.SIMULATE_POLICY:
        if depends_on.get(constants.AFFINITY) == constants.SIMULATE_POLICY:
            return simulate_policy_task.SimulatePolicyTask(
                **common_args, simulate_policy_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return simulate_policy_for_account_task.SimulatePolicyForAccountTask(
                **common_args,
                simulate_policy_name=depends_on.get("name"),
                account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return simulate_policy_for_region_task.SimulatePolicyForRegionTask(
                **common_args,
                simulate_policy_name=depends_on.get("name"),
                region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return simulate_policy_for_account_and_region_task.SimulatePolicyForAccountAndRegionTask(
                **common_args,
                simulate_policy_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )

    elif is_running_in_hub and depends_on.get("type") == constants.CODE_BUILD_RUN:
        if depends_on.get(constants.AFFINITY) == constants.CODE_BUILD_RUN:
            return code_build_run_task.CodeBuildRunTask(
                **common_args, code_build_run_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return code_build_run_for_account_task.CodeBuildRunForAccountTask(
                **common_args,
                code_build_run_name=depends_on.get("name"),
                account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return code_build_run_for_region_task.CodeBuildRunForRegionTask(
                **common_args,
                code_build_run_name=depends_on.get("name"),
                region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return code_build_run_for_account_and_region_task.CodeBuildRunForAccountAndRegionTask(
                **common_args,
                code_build_run_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )

    elif is_running_in_hub and depends_on.get("type") == constants.LAMBDA_INVOCATION:
        if depends_on.get(constants.AFFINITY) == constants.LAMBDA_INVOCATION:
            return lambda_invocation_task.LambdaInvocationTask(
                **common_args, lambda_invocation_name=depends_on.get("name"),
            )
        if depends_on.get(constants.AFFINITY) == "account":
            return lambda_invocation_for_account_task.LambdaInvocationForAccountTask(
                **common_args,
                lambda_invocation_name=depends_on.get("name"),
                account_id=account_id,
            )
        if depends_on.get(constants.AFFINITY) == "region":
            return lambda_invocation_for_region_task.LambdaInvocationForRegionTask(
                **common_args,
                lambda_invocation_name=depends_on.get("name"),
                region=region,
            )
        if depends_on.get(constants.AFFINITY) == "account-and-region":
            return lambda_invocation_for_account_and_region_task.LambdaInvocationForAccountAndRegionTask(
                **common_args,
                lambda_invocation_name=depends_on.get("name"),
                account_id=account_id,
                region=region,
            )

    raise Exception(f"Unhandled: {depends_on}")


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
            self.ou_name if hasattr(self, "ou_name") else "",
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
