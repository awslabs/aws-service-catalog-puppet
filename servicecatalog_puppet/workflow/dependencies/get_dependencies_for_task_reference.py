#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from servicecatalog_puppet import constants
from servicecatalog_puppet import yaml_utils


def get_dependencies_for_task_reference(
    manifest_task_reference_file_path, task_reference, puppet_account_id
):
    dependencies = dict()
    reference = yaml_utils.load(
        open(manifest_task_reference_file_path, "r").read()
    ).get("all_tasks")
    this_task = reference.get(task_reference)
    for dependency_by_reference in this_task.get("dependencies_by_reference", []):
        dependency_by_reference_params = reference.get(dependency_by_reference)
        t_reference = dependency_by_reference_params.get("task_reference")
        dependencies[t_reference] = create(
            manifest_task_reference_file_path,
            puppet_account_id,
            dependency_by_reference_params,
        )
    return dependencies


def create(
    manifest_task_reference_file_path, puppet_account_id, parameters_to_use,
):
    # TODO add in support for list launches and dry run
    section_name = parameters_to_use.get("section_name")
    common_parameters = dict(
        puppet_account_id=puppet_account_id,
        task_reference=parameters_to_use.get("task_reference"),
        manifest_task_reference_file_path=manifest_task_reference_file_path,
        dependencies_by_reference=parameters_to_use.get("dependencies_by_reference"),
        account_id=parameters_to_use.get("account_id"),
        region=parameters_to_use.get("region"),
    )
    manifest_file_path = manifest_task_reference_file_path.replace(
        "manifest-task-reference.yaml", "manifest-expanded.yaml"
    )

    status = parameters_to_use.get("status")
    if section_name == constants.STACKS:
        if status == "terminated":
            from servicecatalog_puppet.workflow.stack.terminate_stack_task import (
                TerminateStackTask,
            )

            return TerminateStackTask(
                **common_parameters,
                stack_name=parameters_to_use.get("stack_name"),
                bucket=parameters_to_use.get("bucket"),
                key=parameters_to_use.get("key"),
                version_id=parameters_to_use.get("version_id"),
                launch_name=parameters_to_use.get("launch_name"),
                stack_set_name=parameters_to_use.get("stack_set_name"),
                capabilities=parameters_to_use.get("capabilities"),
                ssm_param_inputs=[],
                launch_parameters=parameters_to_use.get("launch_parameters"),
                manifest_parameters=parameters_to_use.get(""),
                account_parameters=parameters_to_use.get(""),
                retry_count=parameters_to_use.get("retry_count"),
                worker_timeout=parameters_to_use.get("worker_timeout"),
                ssm_param_outputs=[],
                requested_priority=parameters_to_use.get("requested_priority"),
                use_service_role=parameters_to_use.get("use_service_role"),
                execution=parameters_to_use.get("execution"),
                manifest_file_path=manifest_file_path,
            )
        else:
            from servicecatalog_puppet.workflow.stack.provision_stack_task import (
                ProvisionStackTask,
            )

            return ProvisionStackTask(
                **common_parameters,
                stack_name=parameters_to_use.get("stack_name"),
                bucket=parameters_to_use.get("bucket"),
                key=parameters_to_use.get("key"),
                version_id=parameters_to_use.get("version_id"),
                launch_name=parameters_to_use.get("launch_name"),
                stack_set_name=parameters_to_use.get("stack_set_name"),
                capabilities=parameters_to_use.get("capabilities"),
                ssm_param_inputs=[],
                launch_parameters=parameters_to_use.get("launch_parameters"),
                manifest_parameters=parameters_to_use.get(""),
                account_parameters=parameters_to_use.get(""),
                retry_count=parameters_to_use.get("retry_count"),
                worker_timeout=parameters_to_use.get("worker_timeout"),
                ssm_param_outputs=[],
                requested_priority=parameters_to_use.get("requested_priority"),
                use_service_role=parameters_to_use.get("use_service_role"),
                execution=parameters_to_use.get("execution"),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.LAUNCHES:
        if status == "terminated":
            from servicecatalog_puppet.workflow.launch.do_terminate_product_task import (
                DoTerminateProductTask,
            )

            return DoTerminateProductTask(
                **common_parameters,
                launch_name=parameters_to_use.get("launch_name"),
                portfolio=parameters_to_use.get("portfolio"),
                product=parameters_to_use.get("product"),
                version=parameters_to_use.get("version"),
                # ssm_param_inputs = luigi.ListParameter(default=[], significant=False)
                # launch_parameters = luigi.DictParameter(default={}, significant=False)
                # manifest_parameters = luigi.DictParameter(default={}, significant=False)
                # account_parameters = luigi.DictParameter(default={}, significant=False)
                retry_count=parameters_to_use.get("retry_count"),
                worker_timeout=parameters_to_use.get("worker_timeout"),
                # ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
                requested_priority=parameters_to_use.get("requested_priority"),
                execution=parameters_to_use.get("execution"),
                manifest_file_path=manifest_file_path,
            )
        else:
            from servicecatalog_puppet.workflow.launch.provision_product_task import (
                ProvisionProductTask,
            )

            # TODO
            raise Exception(
                "need to make work with CreateSpokeLocalPortfolioTask, add sharing and associations explicitly through here"
            )

            return ProvisionProductTask(
                **common_parameters,
                launch_name=parameters_to_use.get("launch_name"),
                portfolio=parameters_to_use.get("portfolio"),
                product=parameters_to_use.get("product"),
                version=parameters_to_use.get("version"),
                # ssm_param_inputs = luigi.ListParameter(default=[], significant=False)
                # launch_parameters = luigi.DictParameter(default={}, significant=False)
                # manifest_parameters = luigi.DictParameter(default={}, significant=False)
                # account_parameters = luigi.DictParameter(default={}, significant=False)
                retry_count=parameters_to_use.get("retry_count"),
                worker_timeout=parameters_to_use.get("worker_timeout"),
                # ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
                requested_priority=parameters_to_use.get("requested_priority"),
                execution=parameters_to_use.get("execution"),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.SSM_PARAMETERS:
        from servicecatalog_puppet.workflow.ssm import get_ssm_parameter_task

        return get_ssm_parameter_task.GetSSMParameterTask(
            **common_parameters, param_name=parameters_to_use.get("param_name"),
        )
    elif section_name == constants.SSM_OUTPUTS:
        from servicecatalog_puppet.workflow.ssm import ssm_outputs_task

        return ssm_outputs_task.SSMOutputsTasks(
            **common_parameters,
            param_name=parameters_to_use.get("param_name"),
            stack_output=parameters_to_use.get("stack_output"),
            task_generating_output=parameters_to_use.get("task_generating_output"),
            force_operation=parameters_to_use.get("force_operation"),
        )
    elif section_name == constants.TAG_POLICIES:
        if status == "terminated":
            raise Exception(
                "No supported yet, raise a github issue if you would like to see this"
            )

        else:
            from servicecatalog_puppet.workflow.tag_policies import (
                do_execute_tag_policies_task,
            )

            # TODO test different tag policy deploy to clauses
            return do_execute_tag_policies_task.DoExecuteTagPoliciesTask(
                **common_parameters,
                tag_policy_name=parameters_to_use.get("tag_policy_name"),
                ou_name=parameters_to_use.get("ou_name"),
                content=parameters_to_use.get("content"),
                description=parameters_to_use.get("description"),
                requested_priority=parameters_to_use.get(
                    "requested_priority"
                ),  # TODO make generic
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.SERVICE_CONTROL_POLICIES:
        if status == "terminated":
            from servicecatalog_puppet.workflow.service_control_policies import (
                do_terminate_service_control_policies_task,
            )

            # TODO test different tag policy deploy to clauses
            return do_terminate_service_control_policies_task.DoTerminateServiceControlPoliciesTask(
                **common_parameters,
                service_control_policy_name=parameters_to_use.get(
                    "service_control_policy_name"
                ),
                ou_name=parameters_to_use.get("ou_name"),
                content=parameters_to_use.get("content"),
                description=parameters_to_use.get("description"),
                requested_priority=parameters_to_use.get(
                    "requested_priority"
                ),  # TODO make generic
                manifest_file_path=manifest_file_path,
            )
        else:
            from servicecatalog_puppet.workflow.service_control_policies import (
                do_execute_service_control_policies_task,
            )

            # TODO test different tag policy deploy to clauses
            return do_execute_service_control_policies_task.DoExecuteServiceControlPoliciesTask(
                **common_parameters,
                service_control_policy_name=parameters_to_use.get(
                    "service_control_policy_name"
                ),
                ou_name=parameters_to_use.get("ou_name"),
                content=parameters_to_use.get("content"),
                description=parameters_to_use.get("description"),
                requested_priority=parameters_to_use.get(
                    "requested_priority"
                ),  # TODO make generic
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.ASSERTIONS:
        from servicecatalog_puppet.workflow.assertions import do_assert_task

        return do_assert_task.DoAssertTask(
            **common_parameters,
            assertion_name=parameters_to_use.get("assertion_name"),
            execution=parameters_to_use.get("execution"),
            expected=parameters_to_use.get("expected"),
            actual=parameters_to_use.get("actual"),
            requested_priority=parameters_to_use.get("requested_priority"),
            manifest_file_path=manifest_file_path,
        )

    elif section_name == constants.SIMULATE_POLICIES:
        from servicecatalog_puppet.workflow.simulate_policies import (
            do_execute_simulate_policy_task,
        )

        return do_execute_simulate_policy_task.DoExecuteSimulatePolicyTask(
            **common_parameters,
            simulate_policy_name=parameters_to_use.get("simulate_policy_name"),
            execution=parameters_to_use.get("execution"),
            requested_priority=parameters_to_use.get("requested_priority"),
            simulation_type=parameters_to_use.get("simulation_type"),
            policy_source_arn=parameters_to_use.get("policy_source_arn"),
            policy_input_list=parameters_to_use.get("policy_input_list"),
            permissions_boundary_policy_input_list=parameters_to_use.get(
                "permissions_boundary_policy_input_list"
            ),
            action_names=parameters_to_use.get("action_names"),
            expected_decision=parameters_to_use.get("expected_decision"),
            resource_arns=parameters_to_use.get("resource_arns"),
            resource_policy=parameters_to_use.get("resource_policy"),
            resource_owner=parameters_to_use.get("resource_owner"),
            caller_arn=parameters_to_use.get("caller_arn"),
            context_entries=parameters_to_use.get("context_entries"),
            resource_handling_option=parameters_to_use.get("resource_handling_option"),
            manifest_file_path=manifest_file_path,
        )

    elif section_name == constants.LAMBDA_INVOCATIONS:
        from servicecatalog_puppet.workflow.lambda_invocations import (
            do_invoke_lambda_task,
        )

        return do_invoke_lambda_task.DoInvokeLambdaTask(
            **common_parameters,
            lambda_invocation_name=parameters_to_use.get("lambda_invocation_name"),
            function_name=parameters_to_use.get("function_name"),
            qualifier=parameters_to_use.get("qualifier"),
            invocation_type=parameters_to_use.get("invocation_type"),
            manifest_file_path=manifest_file_path,
        )

    elif section_name == constants.CODE_BUILD_RUNS:
        from servicecatalog_puppet.workflow.codebuild_runs import (
            do_execute_code_build_run_task,
        )

        return do_execute_code_build_run_task.DoExecuteCodeBuildRunTask(
            **common_parameters,
            code_build_run_name=parameters_to_use.get("code_build_run_name"),
            project_name=parameters_to_use.get("project_name"),
            manifest_file_path=manifest_file_path,
        )

    elif section_name == constants.SPOKE_LOCAL_PORTFOLIOS:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
                create_spoke_local_portfolio_task,
            )

            return create_spoke_local_portfolio_task.CreateSpokeLocalPortfolioTask(
                **common_parameters,
                portfolio=parameters_to_use.get("portfolio"),
                provider_name=parameters_to_use.get("provider_name"),
                description=parameters_to_use.get("description"),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.PORTFOLIO_ASSOCIATIONS:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            from servicecatalog_puppet.workflow.portfolio.associations import (
                create_associations_for_spoke_local_portfolio_task,
            )

            return create_associations_for_spoke_local_portfolio_task.CreateAssociationsForSpokeLocalPortfolioTask(
                **common_parameters,
                spoke_local_portfolio_name=parameters_to_use.get(
                    "spoke_local_portfolio_name"
                ),
                associations=parameters_to_use.get("associations"),
                portfolio=parameters_to_use.get("portfolio"),
                portfolio_task_reference=parameters_to_use.get(
                    "portfolio_task_reference"
                ),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.PORTFOLIO_CONSTRAINTS_LAUNCH:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            from servicecatalog_puppet.workflow.portfolio.constraints_management import (
                create_launch_role_constraints_for_spoke_local_portfolio_task,
            )

            return create_launch_role_constraints_for_spoke_local_portfolio_task.CreateLaunchRoleConstraintsForSpokeLocalPortfolioTask(
                **common_parameters,
                spoke_local_portfolio_name=parameters_to_use.get(
                    "spoke_local_portfolio_name"
                ),
                launch_constraints=parameters_to_use.get("launch_constraints"),
                portfolio=parameters_to_use.get("portfolio"),
                portfolio_task_reference=parameters_to_use.get(
                    "portfolio_task_reference"
                ),
                portfolio_get_all_products_and_their_versions_ref=parameters_to_use.get(
                    "portfolio_get_all_products_and_their_versions_ref"
                ),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.PORTFOLIO_CONSTRAINTS_RESOURCE_UPDATE:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            from servicecatalog_puppet.workflow.portfolio.constraints_management import (
                create_resource_update_constraints_for_spoke_local_portfolio_task,
            )

            return create_resource_update_constraints_for_spoke_local_portfolio_task.CreateUpdateResourceConstraintsForSpokeLocalPortfolioTask(
                **common_parameters,
                spoke_local_portfolio_name=parameters_to_use.get(
                    "spoke_local_portfolio_name"
                ),
                resource_update_constraints=parameters_to_use.get(
                    "resource_update_constraints"
                ),
                portfolio=parameters_to_use.get("portfolio"),
                portfolio_task_reference=parameters_to_use.get(
                    "portfolio_task_reference"
                ),
                portfolio_get_all_products_and_their_versions_ref=parameters_to_use.get(
                    "portfolio_get_all_products_and_their_versions_ref"
                ),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.PORTFOLIO_COPY:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            from servicecatalog_puppet.workflow.portfolio.portfolio_management import (
                copy_into_spoke_local_portfolio_task,
            )

            return copy_into_spoke_local_portfolio_task.CopyIntoSpokeLocalPortfolioTask(
                **common_parameters,
                portfolio_task_reference=parameters_to_use.get(
                    "portfolio_task_reference"
                ),
                portfolio_get_all_products_and_their_versions_ref=parameters_to_use.get(
                    "portfolio_get_all_products_and_their_versions_ref"
                ),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.PORTFOLIO_SHARE_AND_ACCEPT_ACCOUNT:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            from servicecatalog_puppet.workflow.portfolio.sharing_management import (
                share_and_accept_portfolio_task,
            )

            return share_and_accept_portfolio_task.ShareAndAcceptPortfolioTask(
                **common_parameters,
                portfolio=parameters_to_use.get("portfolio"),
                sharing_mode=constants.SHARING_MODE_ACCOUNT,
                portfolio_task_reference=parameters_to_use.get(
                    "portfolio_task_reference"
                ),
                manifest_file_path=manifest_file_path,
            )

    elif section_name == constants.PORTFOLIO_GET_ALL_PRODUCTS_AND_THEIR_VERSIONS:
        if status == "terminated":
            raise Exception("Not supported yet")
        else:
            from servicecatalog_puppet.workflow.portfolio.accessors import (
                get_all_products_and_their_versions_task,
            )

            return get_all_products_and_their_versions_task.GetAllProductsAndTheirVersionsTask(
                **common_parameters,
                portfolio=parameters_to_use.get("portfolio"),
                portfolio_task_reference=parameters_to_use.get(
                    "portfolio_task_reference"
                ),
            )

    else:
        raise Exception(f"Unknown section_name: {section_name}")
