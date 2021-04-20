from servicecatalog_puppet import constants


class DependenciesMixin(object):
    def get_section_dependencies(self):
        from servicecatalog_puppet.workflow import codebuild_runs
        from servicecatalog_puppet.workflow import launch
        from servicecatalog_puppet.workflow import spoke_local_portfolios
        from servicecatalog_puppet.workflow import assertions
        from servicecatalog_puppet.workflow import lambda_invocations

        these_dependencies = list()

        if isinstance(self, codebuild_runs.ExecuteCodeBuildRunTask):
            item_name = self.code_build_run_name
        elif isinstance(self, launch.ProvisionProductTask):
            item_name = self.launch_name
        elif isinstance(self, spoke_local_portfolios.SharePortfolioWithSpokeTask):
            item_name = self.spoke_local_portfolio_name
        elif isinstance(self, assertions.AssertionTask):
            item_name = self.assertion_name
        elif isinstance(self, lambda_invocations.InvokeLambdaTask):
            item_name = self.lambda_invocation_name

        dependencies = self.manifest.get(self.section_name).get(item_name).get("depends_on", [])

        common_args = dict(
            manifest_file_path=self.manifest_file_path,
            puppet_account_id=self.puppet_account_id,
        )

        for depends_on in dependencies:
            if depends_on.get("type") == constants.LAUNCH:
                if depends_on.get(constants.AFFINITY) == constants.LAUNCH:
                    these_dependencies.append(
                        launch.LaunchTask(
                            **common_args,
                            launch_name=depends_on.get("name"),
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account":
                    these_dependencies.append(
                        launch.LaunchForAccountTask(
                            **common_args,
                            launch_name=depends_on.get("name"),
                            account_id=self.account_id,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        launch.LaunchForRegionTask(
                            **common_args,
                            launch_name=depends_on.get("name"),
                            region=self.region,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account-and-region":
                    these_dependencies.append(
                        launch.LaunchForAccountAndRegionTask(
                            **common_args,
                            launch_name=depends_on.get("name"),
                            account_id=self.account_id,
                            region=self.region,
                        )
                    )

            elif depends_on.get("type") == constants.SPOKE_LOCAL_PORTFOLIO:
                if depends_on.get(constants.AFFINITY) == constants.SPOKE_LOCAL_PORTFOLIO:
                    these_dependencies.append(
                        spoke_local_portfolios.SpokeLocalPortfolioTask(
                            **common_args,
                            spoke_local_portfolio_name=depends_on.get("name"),
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account":
                    these_dependencies.append(
                        spoke_local_portfolios.SpokeLocalPortfolioForAccountTask(
                            **common_args,
                            spoke_local_portfolio_name=depends_on.get("name"),
                            account_id=self.account_id,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        spoke_local_portfolios.SpokeLocalPortfolioForRegionTask(
                            **common_args,
                            spoke_local_portfolio_name=depends_on.get("name"),
                            region=self.region,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account-and-region":
                    these_dependencies.append(
                        spoke_local_portfolios.SpokeLocalPortfolioForAccountAndRegionTask(
                            **common_args,
                            spoke_local_portfolio_name=depends_on.get("name"),
                            account_id=self.account_id,
                            region=self.region,
                        )
                    )

            elif depends_on.get("type") == constants.ASSERTION:
                if depends_on.get(constants.AFFINITY) == constants.ASSERTION:
                    these_dependencies.append(
                        assertions.AssertionTask(
                            **common_args,
                            assertion_name=depends_on.get("name"),
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account":
                    these_dependencies.append(
                        assertions.AssertionForAccountTask(
                            **common_args,
                            assertion_name=depends_on.get("name"),
                            account_id=self.account_id,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        assertions.AssertionForRegionTask(
                            **common_args,
                            assertion_name=depends_on.get("name"),
                            region=self.region,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account-and-region":
                    these_dependencies.append(
                        assertions.AssertionForAccountAndRegionTask(
                            **common_args,
                            assertion_name=depends_on.get("name"),
                            account_id=self.account_id,
                            region=self.region,
                        )
                    )

            elif depends_on.get("type") == constants.CODE_BUILD_RUN:
                if depends_on.get(constants.AFFINITY) == constants.CODE_BUILD_RUN:
                    these_dependencies.append(
                        codebuild_runs.CodeBuildRunTask(
                            **common_args,
                            code_build_run_name=depends_on.get("name"),
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account":
                    these_dependencies.append(
                        codebuild_runs.CodeBuildRunForAccountTask(
                            **common_args,
                            code_build_run_name=depends_on.get("name"),
                            account_id=self.account_id,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        codebuild_runs.CodeBuildRunForRegionTask(
                            **common_args,
                            code_build_run_name=depends_on.get("name"),
                            region=self.region,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account-and-region":
                    these_dependencies.append(
                        codebuild_runs.CodeBuildRunForAccountAndRegionTask(
                            **common_args,
                            code_build_run_name=depends_on.get("name"),
                            account_id=self.account_id,
                            region=self.region,
                        )
                    )

            elif depends_on.get("type") == constants.LAMBDA_INVOCATION:
                if depends_on.get(constants.AFFINITY) == constants.LAMBDA_INVOCATION:
                    these_dependencies.append(
                        lambda_invocations.LambdaInvocationTask(
                            **common_args,
                            lambda_invocation_name=depends_on.get("name"),
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account":
                    these_dependencies.append(
                        lambda_invocations.LambdaInvocationForAccountTask(
                            **common_args,
                            lambda_invocation_name=depends_on.get("name"),
                            account_id=self.account_id,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "region":
                    these_dependencies.append(
                        lambda_invocations.LambdaInvocationForRegionTask(
                            **common_args,
                            lambda_invocation_name=depends_on.get("name"),
                            region=self.region,
                        )
                    )
                if depends_on.get(constants.AFFINITY) == "account-and-region":
                    these_dependencies.append(
                        lambda_invocations.LambdaInvocationForAccountAndRegionTask(
                            **common_args,
                            lambda_invocation_name=depends_on.get("name"),
                            account_id=self.account_id,
                            region=self.region,
                        )
                    )

        return these_dependencies
