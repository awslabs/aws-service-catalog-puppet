import json

import luigi

from servicecatalog_puppet import config
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import manifest as manifest_tasks
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow import tasks as workflow_tasks


class LambdaInvocationBaseTask(workflow_tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()

    @property
    def section_name(self):
        return constants.LAMBDA_INVOCATIONS


class InvokeLambdaTask(workflow_tasks.PuppetTask, manifest_tasks.ManifestMixen):
    lambda_invocation_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    function_name = luigi.Parameter()
    qualifier = luigi.Parameter()
    invocation_type = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    launch_parameters = luigi.DictParameter()
    manifest_parameters = luigi.DictParameter()
    account_parameters = luigi.DictParameter()

    all_params = []

    manifest_file_path = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "account_id": self.account_id,
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
                )
        self.all_params = all_params

        return dict(
            ssm_params=ssm_params,
        )

    def get_all_params(self):
        all_params = {}
        self.info(f"collecting all_params")
        for param_name, param_details in self.all_params.items():
            if param_details.get("ssm"):
                with self.input().get("ssm_params").get(param_name).open() as f:
                    all_params[param_name] = json.loads(f.read()).get("Value")
            if param_details.get("default"):
                all_params[param_name] = param_details.get("default")
            if param_details.get("mapping"):
                all_params[param_name] = self.manifest.get_mapping(
                    param_details.get("mapping"), self.account_id, self.region
                )

        self.info(f"finished collecting all_params: {all_params}")
        return all_params

    def run(self):
        home_region = config.get_home_region(self.puppet_account_id)
        with self.hub_regional_client(
            "lambda", region_name=home_region
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


class LambdaInvocationForTask(LambdaInvocationBaseTask, manifest_tasks.ManifestMixen):
    lambda_invocation_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def get_klass_for_provisioning(self):
        return InvokeLambdaTask

    def run(self):
        self.write_output(self.params_for_results_display())


class LambdaInvocationForRegionTask(LambdaInvocationForTask):
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        these_dependencies = list()
        requirements = dict(
            dependencies=dependencies, these_dependencies=these_dependencies,
        )

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
                self.puppet_account_id, self.section_name, self.lambda_invocation_name, self.region
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )


        return requirements


class LambdaInvocationForAccountTask(LambdaInvocationForTask):
    account_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies,)

        klass = self.get_klass_for_provisioning()

        for task in self.manifest.get_tasks_for_launch_and_region(
                self.puppet_account_id, self.section_name, self.lambda_invocation_name, self.account_id
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class LambdaInvocationForAccountAndRegionTask(LambdaInvocationForTask):
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        dependencies = list()
        requirements = dict(dependencies=dependencies)

        klass = self.get_klass_for_provisioning()

        for (
                task
        ) in self.manifest.get_tasks_for_launch_and_account_and_region(
            self.puppet_account_id, self.section_name, self.lambda_invocation_name, self.account_id, self.region,
        ):
            dependencies.append(
                klass(**task, manifest_file_path=self.manifest_file_path)
            )

        return requirements


class LambdaInvocationTask(LambdaInvocationForTask):

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        regional_dependencies = list()
        account_dependencies = list()
        account_and_region_dependencies = list()
        requirements = dict(
            regional_launches=regional_dependencies,
            account_launches=account_dependencies,
            account_and_region_dependencies=account_and_region_dependencies,
        )
        for region in self.manifest.get_regions_used_for_section_item(
                self.puppet_account_id, self.section_name, self.lambda_invocation_name
        ):
            regional_dependencies.append(
                LambdaInvocationForRegionTask(**self.param_kwargs, region=region, )
            )

        for account_id in self.manifest.get_account_ids_used_for_section_item(
                self.puppet_account_id, self.section_name, self.lambda_invocation_name
        ):
            account_dependencies.append(
                LambdaInvocationForAccountTask(
                    **self.param_kwargs, account_id=account_id,
                )
            )

        for (
                account_id,
                regions,
        ) in self.manifest.get_account_ids_and_regions_used_for_section_item(
            self.puppet_account_id, self.section_name, self.lambda_invocation_name
        ).items():
            for region in regions:
                account_and_region_dependencies.append(
                    LambdaInvocationForAccountAndRegionTask(
                        **self.param_kwargs,
                        account_id=account_id,
                        region=region,
                    )
                )

        return requirements

    def run(self):
        self.write_output(self.params_for_results_display())


class LambdaInvocationsSectionTask(LambdaInvocationBaseTask, manifest_tasks.SectionTask):
    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        requirements = dict(
            invocations=[
                LambdaInvocationTask(
                    lambda_invocation_name=lambda_invocation_name,
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                )
                for lambda_invocation_name, lambda_invocation in self.manifest.get(
                    self.section_name, {}
                ).items()
            ]
        )
        return requirements

    def run(self):
        self.write_output(self.manifest.get("lambda-invocations"))
