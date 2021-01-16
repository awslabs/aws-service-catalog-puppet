import json

import luigi

from servicecatalog_puppet.workflow import tasks as workflow_tasks
from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow.provisioning import LaunchTask
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet import config
from betterboto import client as betterboto_client


class InvokeLambdaTask(workflow_tasks.PuppetTask, manifest_tasks.ManifestMixen):
    lambda_invocation_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    function_name = luigi.Parameter()
    qualifier = luigi.Parameter()
    invocation_type = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    parameters = luigi.DictParameter()

    launch_parameters = luigi.DictParameter()
    manifest_parameters = luigi.DictParameter()
    account_parameters = luigi.DictParameter()

    all_params = []

    manifest_file_path = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "lambda_invocation_name": self.lambda_invocation_name,
            "account_id": self.account_id,
            "region": self.region,
            "function_name": self.function_name,
            "qualifier": self.qualifier,
            "invocation_type": self.invocation_type,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        all_params = dict()
        all_params.update(self.manifest_parameters)
        all_params.update(self.launch_parameters)
        all_params.update(self.account_parameters)

        ssm_params = dict()
        for param_name, param_details in all_params.items():
            if param_details.get("ssm"):
                if param_details.get("default"):
                    del param_details["default"]
                ssm_parameter_name = param_details.get("ssm").get("name")
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::Region}", self.region
                )
                ssm_parameter_name = ssm_parameter_name.replace(
                    "${AWS::AccountId}", self.account_id
                )
                ssm_params[param_name] = tasks.GetSSMParamTask(
                    parameter_name=param_name,
                    name=ssm_parameter_name,
                    region=param_details.get("ssm").get(
                        "region", config.get_home_region(self.puppet_account_id)
                    ),
                    cache_invalidator=self.cache_invalidator,
                )
        self.all_params = all_params

        return dict(
            ssm_params=ssm_params,
            dependencies=LambdaInvocationDependenciesWrapperTask(
                lambda_invocation_name=self.lambda_invocation_name,
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                should_use_sns=self.should_use_sns,
                should_use_product_plans=self.should_use_product_plans,
                include_expanded_from=self.include_expanded_from,
                single_account=self.single_account,
                is_dry_run=self.is_dry_run,
                cache_invalidator=self.cache_invalidator,
            ),
        )

    def get_all_params(self):
        all_params = dict()
        for param_name, param_details in self.parameters.items():
            if param_details.get("ssm"):
                with self.input().get("ssm_params").get(param_name).open() as f:
                    all_params[param_name] = json.loads(f.read()).get("Value")
            if param_details.get("default"):
                all_params[param_name] = param_details.get("default")
            if param_details.get("mapping"):
                all_params[param_name] = self.manifest.get_mapping(
                    param_details.get("mapping"), self.account_id, self.region
                )

        return all_params

    def run(self):
        home_region = config.get_home_region(self.puppet_account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "lambda",
            config.get_puppet_role_arn(self.puppet_account_id),
            f"sc-{home_region}-{self.puppet_account_id}",
            region_name=home_region,
        ) as lambda_client:
            payload = dict(
                account_id=self.account_id,
                region=self.region,
                parameters=self.get_all_params(),
            )
            response = lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType=self.invocation_type,
                Payload=json.dumps(payload),
                Qualifier=self.qualifier,
            )
        success_results = dict(RequestResponse=200, Event=202, DryRun=204)

        if success_results.get(self.invocation_type) != response.get("StatusCode"):
            raise Exception(
                f"{self.lambda_invocation_name} failed for {self.account_id}, {self.region}"
            )
        else:
            if response.get("FunctionError"):
                error_payload = response.get("Payload").read()
                raise Exception(error_payload)
            else:
                output = dict(
                    **self.params_for_results_display(),
                    payload=payload,
                    response=response,
                )
                self.write_output(output)


class LambdaInvocationDependenciesWrapperTask(
    workflow_tasks.PuppetTask, manifest_tasks.ManifestMixen
):
    lambda_invocation_name = luigi.Parameter()
    manifest_file_path = luigi.Parameter()

    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "lambda_invocation_name": self.lambda_invocation_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        lambda_invocation = self.manifest.get("lambda-invocations").get(
            self.lambda_invocation_name
        )

        dependencies = list()
        for dependency in lambda_invocation.get("depends_on", []):
            if isinstance(dependency, str):
                dependencies.append(
                    LaunchTask(
                        launch_name=dependency,
                        manifest_file_path=self.manifest_file_path,
                        puppet_account_id=self.puppet_account_id,
                        should_use_sns=self.should_use_sns,
                        should_use_product_plans=self.should_use_product_plans,
                        include_expanded_from=self.include_expanded_from,
                        single_account=self.single_account,
                        is_dry_run=self.is_dry_run,
                        execution_mode="hub",
                        cache_invalidator=self.cache_invalidator,
                    )
                )
            else:
                dependency_type = dependency.get("type", "launch")
                if dependency_type == "launch":
                    dependencies.append(
                        LaunchTask(
                            launch_name=dependency.get("name"),
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            should_use_sns=self.should_use_sns,
                            should_use_product_plans=self.should_use_product_plans,
                            include_expanded_from=self.include_expanded_from,
                            single_account=self.single_account,
                            is_dry_run=self.is_dry_run,
                            execution_mode="hub",
                            cache_invalidator=self.cache_invalidator,
                        )
                    )
                elif dependency_type == "lambda-invocation":
                    dependencies.append(
                        LambdaInvocationTask(
                            lambda_invocation_name=dependency.get("name"),
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            should_use_sns=self.should_use_sns,
                            should_use_product_plans=self.should_use_product_plans,
                            include_expanded_from=self.include_expanded_from,
                            single_account=self.single_account,
                            is_dry_run=self.is_dry_run,
                            cache_invalidator=self.cache_invalidator,
                        )
                    )
        return dependencies

    def run(self):
        self.write_output(self.params_for_results_display())


class LambdaInvocationTask(workflow_tasks.PuppetTask, manifest_tasks.ManifestMixen):
    lambda_invocation_name = luigi.Parameter()
    manifest_file_path = luigi.Parameter()

    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "lambda_invocation_name": self.lambda_invocation_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = list()
        lambda_invocation = self.manifest.get("lambda-invocations").get(
            self.lambda_invocation_name
        )

        task_defs = self.manifest.get_task_defs_from_details(
            self.puppet_account_id,
            True,
            self.lambda_invocation_name,
            {},
            "lambda-invocations",
        )

        common_params = {
            "lambda_invocation_name": self.lambda_invocation_name,
            "function_name": lambda_invocation.get("function_name"),
            "qualifier": lambda_invocation.get("qualifier", "$LATEST"),
            "invocation_type": lambda_invocation.get("invocation_type"),
            "puppet_account_id": self.puppet_account_id,
            "parameters": lambda_invocation.get("parameters", {}),
            "launch_parameters": lambda_invocation.get("parameters", {}),
            "manifest_parameters": self.manifest.get("parameters", {}),
        }

        wrapper_params = dict(
            manifest_file_path=self.manifest_file_path,
            should_use_sns=self.should_use_sns,
            should_use_product_plans=self.should_use_product_plans,
            include_expanded_from=self.include_expanded_from,
            single_account=self.single_account,
            is_dry_run=self.is_dry_run,
        )

        for task_def in task_defs:
            task_def_parameters = {
                "account_id": task_def.get("account_id"),
                "region": task_def.get("region"),
                "account_parameters": task_def.get("account_parameters"),
                "cache_invalidator": self.cache_invalidator,
            }
            task_def_parameters.update(common_params)
            task_def_parameters.update(wrapper_params)
            requirements.append(InvokeLambdaTask(**task_def_parameters))
        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


class LambdaInvocationsSectionTask(manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "manifest_file_path": self.manifest_file_path,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = dict(
            invocations=[
                LambdaInvocationTask(
                    lambda_invocation_name=lambda_invocation_name,
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                    should_use_sns=self.should_use_sns,
                    should_use_product_plans=self.should_use_product_plans,
                    include_expanded_from=self.include_expanded_from,
                    single_account=self.single_account,
                    is_dry_run=self.is_dry_run,
                    cache_invalidator=self.cache_invalidator,
                )
                for lambda_invocation_name, lambda_invocation in self.manifest.get(
                    "lambda-invocations", {}
                ).items()
            ]
        )
        return requirements

    def run(self):
        self.write_output(self.manifest.get("lambda-invocations"))
