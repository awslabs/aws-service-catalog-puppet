import json
import os
from functools import lru_cache

import luigi
from betterboto import client as betterboto_client
from servicecatalog_puppet.workflow import generate as generate_tasks

from servicecatalog_puppet import manifest_utils_for_launches
from servicecatalog_puppet import aws
from servicecatalog_puppet import config

from servicecatalog_puppet import constants
from servicecatalog_puppet import manifest_utils
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow import (
    portfoliomanagement as portfoliomanagement_tasks,
)
from servicecatalog_puppet.workflow import manifest as manifest_tasks


class ProvisioningTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()


class ProvisioningArtifactParametersTask(ProvisioningTask):
    puppet_account_id = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product = luigi.Parameter()
    product_id = luigi.Parameter()
    version = luigi.Parameter()
    version_id = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    @property
    def retry_count(self):
        return 5

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "account_id": self.account_id,
            "region": self.region,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_parameters_{self.account_id}_{self.region}",
        ]

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"{self.account_id}-{self.region}-sc",
            region_name=self.region,
        ) as service_catalog:
            self.info(
                f"getting path for {self.product_id} of portfolio: {self.portfolio}"
            )
            path_id = aws.get_path_for_product(
                service_catalog, self.product_id, self.portfolio
            )
            provisioning_artifact_parameters = service_catalog.describe_provisioning_parameters(
                ProductId=self.product_id,
                ProvisioningArtifactId=self.version_id,
                PathId=path_id,
            ).get(
                "ProvisioningArtifactParameters", []
            )
            self.write_output(
                provisioning_artifact_parameters
                if isinstance(provisioning_artifact_parameters, list)
                else [provisioning_artifact_parameters]
            )


class ProvisionProductTask(ProvisioningTask, manifest_tasks.ManifestMixen):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product = luigi.Parameter()
    product_id = luigi.Parameter()
    version = luigi.Parameter()
    version_id = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    puppet_account_id = luigi.Parameter()

    parameters = luigi.ListParameter(default=[], significant=False)
    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    should_use_sns = luigi.BoolParameter(significant=False, default=False)
    should_use_product_plans = luigi.BoolParameter(significant=False, default=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    execution = luigi.Parameter()

    cache_invalidator = luigi.Parameter()

    try_count = 1
    all_params = []

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "execution": self.execution,
            "cache_invalidator": self.cache_invalidator,
        }

    @property
    def priority(self):
        return self.requested_priority

    def requires(self):
        all_params = {}
        all_params.update(self.manifest_parameters)
        all_params.update(self.launch_parameters)
        all_params.update(self.account_parameters)

        ssm_params = {}

        for param_name, param_details in all_params.items():
            if param_details.get("ssm"):
                if param_details.get("default"):
                    del param_details["default"]
                ssm_params[param_name] = tasks.GetSSMParamTask(
                    parameter_name=param_name,
                    name=param_details.get("ssm").get("name"),
                    region=param_details.get("ssm").get(
                        "region", config.get_home_region(self.puppet_account_id)
                    ),
                    cache_invalidator=self.cache_invalidator,
                )
        self.all_params = all_params

        return {
            "ssm_params": ssm_params,
            "provisioning_artifact_parameters": ProvisioningArtifactParametersTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                portfolio_id=self.portfolio_id,
                product=self.product,
                product_id=self.product_id,
                version=self.version,
                version_id=self.version_id,
                account_id=self.account_id,
                region=self.region,
            ),
        }

    def api_calls_used(self):
        return {
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",
            f"cloudformation.get_template_summary_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
            f"servicecatalog.list_provisioned_product_plans_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.delete_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.create_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.execute_provisioned_product_plan_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.provision_product_{self.account_id}_{self.region}",
            # f"ssm.put_parameter_and_wait_{self.region}",
        }

    def run(self):
        ssm_params = dict()
        task_output = dict(
            **self.params_for_results_display(),
            account_parameters=tasks.unwrap(self.account_parameters),
            launch_parameters=tasks.unwrap(self.launch_parameters),
            manifest_parameters=tasks.unwrap(self.manifest_parameters),
            ssm_params=ssm_params,
        )
        for k, v in self.input().get("ssm_params").items():
            ssm_params[k] = json.loads(v.open("r").read())

        all_params = self.get_all_params()

        role = config.get_puppet_role_arn(self.account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            role,
            f"sc-{self.region}-{self.account_id}",
            region_name=self.region,
        ) as service_catalog:
            path_id = aws.get_path_for_product(
                service_catalog, self.product_id, self.portfolio
            )

            (
                provisioned_product_id,
                provisioning_artifact_id,
            ) = aws.terminate_if_status_is_not_available(
                service_catalog,
                self.launch_name,
                self.product_id,
                self.account_id,
                self.region,
            )
            self.info(
                f"pp_id: {provisioned_product_id}, paid : {provisioning_artifact_id}"
            )

            with betterboto_client.CrossAccountClientContextManager(
                "cloudformation",
                role,
                f"cfn-{self.region}-{self.account_id}",
                region_name=self.region,
            ) as cloudformation:
                need_to_provision = True

                self.info(
                    f"running as {role},checking {self.product_id} {self.version_id} {path_id} in {self.account_id} {self.region}"
                )

                with self.input().get("provisioning_artifact_parameters").open(
                    "r"
                ) as f:
                    provisioning_artifact_parameters = json.loads(f.read())

                params_to_use = {}
                for p in provisioning_artifact_parameters:
                    param_name = p.get("ParameterKey")
                    params_to_use[param_name] = all_params.get(
                        param_name, p.get("DefaultValue")
                    )

                if provisioning_artifact_id == self.version_id:
                    self.info(f"found previous good provision")
                    if provisioned_product_id:
                        self.info(f"checking params for diffs")
                        provisioned_parameters = aws.get_parameters_for_stack(
                            cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}",
                        )
                        self.info(f"current params: {provisioned_parameters}")

                        self.info(f"new params: {params_to_use}")

                        if provisioned_parameters == params_to_use:
                            self.info(f"params unchanged")
                            need_to_provision = False
                        else:
                            self.info(f"params changed")

                if need_to_provision:
                    self.info(
                        f"about to provision with params: {json.dumps(params_to_use)}"
                    )

                    if provisioned_product_id:
                        stack = aws.get_stack_output_for(
                            cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}",
                        )
                        stack_status = stack.get("StackStatus")
                        self.info(f"current cfn stack_status is {stack_status}")
                        if stack_status not in [
                            "UPDATE_COMPLETE",
                            "CREATE_COMPLETE",
                            "UPDATE_ROLLBACK_COMPLETE",
                        ]:
                            raise Exception(
                                f"[{self.uid}] current cfn stack_status is {stack_status}"
                            )
                        if stack_status == "UPDATE_ROLLBACK_COMPLETE":
                            self.warning(
                                f"[{self.uid}] SC-{self.account_id}-{provisioned_product_id} has a status of "
                                f"{stack_status}.  This may need manual resolution."
                            )

                    if provisioned_product_id:
                        if self.should_use_product_plans:
                            provisioned_product_id = aws.provision_product_with_plan(
                                service_catalog,
                                self.launch_name,
                                self.account_id,
                                self.region,
                                self.product_id,
                                self.version_id,
                                self.puppet_account_id,
                                path_id,
                                params_to_use,
                                self.version,
                                self.should_use_sns,
                            )
                        else:
                            provisioned_product_id = aws.update_provisioned_product(
                                service_catalog,
                                self.launch_name,
                                self.account_id,
                                self.region,
                                self.product_id,
                                self.version_id,
                                self.puppet_account_id,
                                path_id,
                                params_to_use,
                                self.version,
                                self.execution,
                            )

                    else:
                        provisioned_product_id = aws.provision_product(
                            service_catalog,
                            self.launch_name,
                            self.account_id,
                            self.region,
                            self.product_id,
                            self.version_id,
                            self.puppet_account_id,
                            path_id,
                            params_to_use,
                            self.version,
                            self.should_use_sns,
                            self.execution,
                        )

                self.info(f"self.execution_mode is {self.execution}")
                if self.execution == constants.EXECUTION_MODE_HUB:
                    self.info(
                        f"Running in execution mode: {self.execution}, checking for SSM outputs"
                    )
                    with betterboto_client.CrossAccountClientContextManager(
                        "cloudformation",
                        role,
                        f"cfn-{self.region}-{self.account_id}",
                        region_name=self.region,
                    ) as spoke_cloudformation:
                        stack_details = aws.get_stack_output_for(
                            spoke_cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}",
                        )

                    for ssm_param_output in self.ssm_param_outputs:
                        self.info(
                            f"writing SSM Param: {ssm_param_output.get('stack_output')}"
                        )
                        with betterboto_client.ClientContextManager("ssm") as ssm:
                            found_match = False
                            # TODO push into another task
                            for output in stack_details.get("Outputs", []):
                                if output.get("OutputKey") == ssm_param_output.get(
                                    "stack_output"
                                ):
                                    found_match = True
                                    self.info(f"found value")
                                    ssm.put_parameter_and_wait(
                                        Name=ssm_param_output.get("param_name"),
                                        Value=output.get("OutputValue"),
                                        Type=ssm_param_output.get(
                                            "param_type", "String"
                                        ),
                                        Overwrite=True,
                                    )
                            if not found_match:
                                raise Exception(
                                    f"[{self.uid}] Could not find match for {ssm_param_output.get('stack_output')}"
                                )

                    self.write_output(task_output)
                else:
                    self.write_output(task_output)
                self.info("finished")

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


class ProvisionProductDryRunTask(ProvisionProductTask):
    def api_calls_used(self):
        return [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",
            f"cloudformation.describe_provisioning_artifact_{self.account_id}_{self.region}",
            f"cloudformation.get_template_summary_{self.account_id}_{self.region}",
            f"cloudformation.describe_stacks_{self.account_id}_{self.region}",
        ]

    def run(self):
        self.info(f"starting deploy try {self.try_count} of {self.retry_count}")

        all_params = self.get_all_params()

        role = config.get_puppet_role_arn(self.account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            role,
            f"sc-{self.region}-{self.account_id}",
            region_name=self.region,
        ) as service_catalog:
            self.info(f"looking for previous failures")
            path_id = aws.get_path_for_product(
                service_catalog, self.product_id, self.portfolio
            )

            response = service_catalog.scan_provisioned_products_single_page(
                AccessLevelFilter={"Key": "Account", "Value": "self"},
            )

            provisioned_product_id = False
            provisioning_artifact_id = False
            current_status = "NOT_PROVISIONED"
            for r in response.get("ProvisionedProducts", []):
                if r.get("Name") == self.launch_name:
                    current_status = r.get("Status")
                    if current_status in ["AVAILABLE", "TAINTED"]:
                        provisioned_product_id = r.get("Id")
                        provisioning_artifact_id = r.get("ProvisioningArtifactId")

            self.info(
                f"pp_id: {provisioned_product_id}, paid : {provisioning_artifact_id}"
            )
            current_version_details = self.get_current_version(
                provisioning_artifact_id, service_catalog
            )

            with betterboto_client.CrossAccountClientContextManager(
                "cloudformation",
                role,
                f"cfn-{self.region}-{self.account_id}",
                region_name=self.region,
            ) as cloudformation:
                self.info(
                    f"running as {role},checking {self.product_id} {self.version_id} {path_id} in {self.account_id} {self.region}"
                )

                with self.input().get("provisioning_artifact_parameters").open(
                    "r"
                ) as f:
                    provisioning_artifact_parameters = json.loads(f.read())

                params_to_use = {}
                for p in provisioning_artifact_parameters:
                    param_name = p.get("ParameterKey")
                    params_to_use[param_name] = all_params.get(
                        param_name, p.get("DefaultValue")
                    )

                if provisioning_artifact_id == self.version_id:
                    self.info(f"found previous good provision")
                    if provisioned_product_id:
                        self.info(f"checking params for diffs")
                        provisioned_parameters = aws.get_parameters_for_stack(
                            cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}",
                        )
                        self.info(f"current params: {provisioned_parameters}")
                        self.info(f"new params: {params_to_use}")

                        if provisioned_parameters == params_to_use:
                            self.info(f"params unchanged")
                            self.write_result(
                                current_version=self.version,
                                new_version=self.version,
                                effect=constants.NO_CHANGE,
                                current_status=current_status,
                                active=current_version_details.get("Active"),
                                notes="Versions and params are the same",
                            )
                        else:
                            self.write_result(
                                current_version=self.version,
                                new_version=self.version,
                                effect=constants.CHANGE,
                                current_status=current_status,
                                active=current_version_details.get("Active"),
                                notes="Versions are the same but the params are different",
                            )
                else:
                    if provisioning_artifact_id:
                        current_version = current_version_details.get("Name")
                        active = current_version_details.get("Active")
                    else:
                        current_version = ""
                        active = False
                    self.write_result(
                        current_version=current_version,
                        new_version=self.version,
                        effect=constants.CHANGE,
                        current_status=current_status,
                        active=active,
                        notes="Version change",
                    )

    def get_current_version(self, provisioning_artifact_id, service_catalog):
        return service_catalog.describe_provisioning_artifact(
            ProvisioningArtifactId=provisioning_artifact_id, ProductId=self.product_id,
        ).get("ProvisioningArtifactDetail")

    def write_result(
        self, current_version, new_version, effect, current_status, active, notes=""
    ):
        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "current_version": current_version,
                        "new_version": new_version,
                        "effect": effect,
                        "current_status": current_status,
                        "active": active,
                        "notes": notes,
                        "params": self.param_kwargs,
                    },
                    indent=4,
                    default=str,
                )
            )


class TerminateProductTask(ProvisioningTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product = luigi.Parameter()
    product_id = luigi.Parameter()
    version = luigi.Parameter()
    version_id = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    retry_count = luigi.IntParameter(default=1)

    ssm_param_outputs = luigi.ListParameter(default=[])

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    try_count = 1

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])

    # dependencies = luigi.ListParameter(default=[])

    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.scan_provisioned_products_single_page{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",
            # f"ssm.delete_parameter_{self.region}": 1,
        ]

    def run(self):
        self.info(f"starting terminate try {self.try_count} of {self.retry_count}")

        role = config.get_puppet_role_arn(self.account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            role,
            f"sc-{self.region}-{self.account_id}",
            region_name=self.region,
        ) as service_catalog:
            self.info(
                f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures"
            )
            provisioned_product_id, provisioning_artifact_id = aws.ensure_is_terminated(
                service_catalog, self.launch_name, self.product_id
            )
            log_output = self.to_str_params()
            log_output.update(
                {"provisioned_product_id": provisioned_product_id,}
            )

            for ssm_param_output in self.ssm_param_outputs:
                param_name = ssm_param_output.get("param_name")
                self.info(
                    f"[{self.launch_name}] {self.account_id}:{self.region} :: deleting SSM Param: {param_name}"
                )
                with betterboto_client.ClientContextManager("ssm") as ssm:
                    try:
                        # todo push into another task
                        ssm.delete_parameter(Name=param_name,)
                        self.info(
                            f"[{self.launch_name}] {self.account_id}:{self.region} :: deleting SSM Param: {param_name}"
                        )
                    except ssm.exceptions.ParameterNotFound:
                        self.info(
                            f"[{self.launch_name}] {self.account_id}:{self.region} :: SSM Param: {param_name} not found"
                        )

            with self.output().open("w") as f:
                f.write(json.dumps(log_output, indent=4, default=str,))

            self.info(
                f"[{self.launch_name}] {self.account_id}:{self.region} :: finished terminating"
            )


class TerminateProductDryRunTask(ProvisioningTask):
    launch_name = luigi.Parameter()
    portfolio = luigi.Parameter()
    portfolio_id = luigi.Parameter()
    product = luigi.Parameter()
    product_id = luigi.Parameter()
    version = luigi.Parameter()
    version_id = luigi.Parameter()

    account_id = luigi.Parameter()
    region = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    retry_count = luigi.IntParameter(default=1)

    ssm_param_outputs = luigi.ListParameter(default=[])

    worker_timeout = luigi.IntParameter(default=0, significant=False)

    parameters = luigi.ListParameter(default=[])
    ssm_param_inputs = luigi.ListParameter(default=[])

    cache_invalidator = luigi.Parameter()

    try_count = 1

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "portfolio": self.portfolio,
            "portfolio_id": self.portfolio_id,
            "product": self.product,
            "product_id": self.product_id,
            "version": self.version,
            "version_id": self.version_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def write_result(self, current_version, new_version, effect, notes=""):
        with self.output().open("w") as f:
            f.write(
                json.dumps(
                    {
                        "current_version": current_version,
                        "new_version": new_version,
                        "effect": effect,
                        "notes": notes,
                        "params": self.param_kwargs,
                    },
                    indent=4,
                    default=str,
                )
            )

    def api_calls_used(self):
        return [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.describe_provisioning_artifact_{self.account_id}_{self.region}",
        ]

    def run(self):
        self.info(
            f"starting dry run terminate try {self.try_count} of {self.retry_count}"
        )

        role = config.get_puppet_role_arn(self.account_id)
        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            role,
            f"sc-{self.region}-{self.account_id}",
            region_name=self.region,
        ) as service_catalog:
            self.info(
                f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures"
            )
            r = aws.get_provisioned_product_details(
                self.product_id, self.launch_name, service_catalog
            )

            if r is None:
                self.write_result(
                    "-", "-", constants.NO_CHANGE, notes="There is nothing to terminate"
                )
            else:
                provisioned_product_name = (
                    service_catalog.describe_provisioning_artifact(
                        ProvisioningArtifactId=r.get("ProvisioningArtifactId"),
                        ProductId=self.product_id,
                    )
                    .get("ProvisioningArtifactDetail")
                    .get("Name")
                )

                if r.get("Status") != "TERMINATED":
                    self.write_result(
                        provisioned_product_name,
                        "-",
                        constants.CHANGE,
                        notes="The product would be terminated",
                    )
                else:
                    self.write_result(
                        "-",
                        "-",
                        constants.CHANGE,
                        notes="The product is already terminated",
                    )


class ResetProvisionedProductOwnerTask(ProvisioningTask):
    launch_name = luigi.Parameter()
    account_id = luigi.Parameter()
    region = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
        }

    def api_calls_used(self):
        return [
            f"servicecatalog.scan_provisioned_products_single_page_{self.account_id}_{self.region}",
            f"servicecatalog.update_provisioned_product_properties_{self.account_id}_{self.region}",
        ]

    def run(self):
        self.info(f"starting ResetProvisionedProductOwnerTask")

        with betterboto_client.CrossAccountClientContextManager(
            "servicecatalog",
            config.get_puppet_role_arn(self.account_id),
            f"sc-{self.region}-{self.account_id}",
            region_name=self.region,
        ) as service_catalog:
            self.info(f"Checking if existing provisioned product exists")
            all_results = service_catalog.scan_provisioned_products_single_page(
                AccessLevelFilter={"Key": "Account", "Value": "self"},
            ).get("ProvisionedProducts", [])
            changes_made = list()
            for result in all_results:
                if result.get("Name") == self.launch_name:
                    provisioned_product_id = result.get("Id")
                    self.info(f"Ensuring current provisioned product owner is correct")
                    changes_made.append(result)
                    service_catalog.update_provisioned_product_properties(
                        ProvisionedProductId=provisioned_product_id,
                        ProvisionedProductProperties={
                            "OWNER": config.get_puppet_role_arn(self.account_id)
                        },
                    )
            self.write_output(changes_made)


class RunDeployInSpokeTask(tasks.PuppetTask):
    manifest_file_path = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    account_id = luigi.Parameter()

    home_region = luigi.Parameter()
    regions = luigi.ListParameter()
    should_collect_cloudformation_events = luigi.BoolParameter()
    should_forward_events_to_eventbridge = luigi.BoolParameter()
    should_forward_failures_to_opscenter = luigi.BoolParameter()

    def params_for_results_display(self):
        return {
            "manifest_file_path": self.manifest_file_path,
            "puppet_account_id": self.puppet_account_id,
            "account_id": self.account_id,
        }

    def run(self):
        with betterboto_client.CrossAccountClientContextManager(
            "s3",
            config.get_puppet_role_arn(self.puppet_account_id),
            f"s3-{self.puppet_account_id}",
        ) as s3:
            bucket = f"sc-puppet-spoke-deploy-{self.puppet_account_id}"
            key = f"{os.getenv('CODEBUILD_BUILD_NUMBER', '0')}.yaml"
            s3.put_object(
                Body=open(self.manifest_file_path).read(), Bucket=bucket, Key=key,
            )
            signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=60 * 60 * 24,
            )
        with betterboto_client.ClientContextManager("ssm") as ssm:
            response = ssm.get_parameter(Name="service-catalog-puppet-version")
            version = response.get("Parameter").get("Value")
        with betterboto_client.CrossAccountClientContextManager(
            "codebuild",
            config.get_puppet_role_arn(self.account_id),
            f"codebuild-{self.account_id}",
        ) as codebuild:
            response = codebuild.start_build(
                projectName=constants.EXECUTION_SPOKE_CODEBUILD_PROJECT_NAME,
                environmentVariablesOverride=[
                    {"name": "VERSION", "value": version, "type": "PLAINTEXT"},
                    {"name": "MANIFEST_URL", "value": signed_url, "type": "PLAINTEXT"},
                    {
                        "name": "PUPPET_ACCOUNT_ID",
                        "value": self.puppet_account_id,
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "HOME_REGION",
                        "value": self.home_region,
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "REGIONS",
                        "value": ",".join(self.regions),
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "SHOULD_COLLECT_CLOUDFORMATION_EVENTS",
                        "value": str(self.should_collect_cloudformation_events),
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "SHOULD_FORWARD_EVENTS_TO_EVENTBRIDGE",
                        "value": str(self.should_forward_events_to_eventbridge),
                        "type": "PLAINTEXT",
                    },
                    {
                        "name": "SHOULD_FORWARD_FAILURES_TO_OPSCENTER",
                        "value": str(self.should_forward_failures_to_opscenter),
                        "type": "PLAINTEXT",
                    },
                ],
            )
        self.write_output(response)


class LaunchInSpokeTask(ProvisioningTask, manifest_tasks.ManifestMixen):
    launch_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()
    execution_mode = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
        }

    def generate_tasks(self, task_defs, manifest):
        self.info("generate_provisions")
        provisions = []
        accounts_by_id = dict()
        for a in manifest.get("accounts"):
            accounts_by_id[a.get("account_id")] = a

        for task_def in task_defs:
            if self.single_account == "None" or self.single_account is None:
                pass
            else:
                if task_def.get("account_id") != self.single_account:
                    continue
            task_status = task_def.get("status")
            del task_def["status"]
            del task_def["depends_on"]
            task_def["is_dry_run"] = self.is_dry_run
            run_deploy_in_spoke_task_params = dict(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=task_def.get("account_id"),
                home_region=config.get_home_region(self.puppet_account_id),
                regions=config.get_regions(self.puppet_account_id),
                should_collect_cloudformation_events=config.get_should_use_sns(
                    self.puppet_account_id
                ),
                should_forward_events_to_eventbridge=config.get_should_use_eventbridge(
                    self.puppet_account_id
                ),
                should_forward_failures_to_opscenter=config.get_should_forward_failures_to_opscenter(
                    self.puppet_account_id
                ),
            )

            if task_status == constants.PROVISIONED:
                provisioning_parameters = {}
                for p in ProvisionProductTask.get_param_names(include_significant=True):
                    provisioning_parameters[p] = task_def.get(p)

                if self.is_dry_run:
                    provisions.append(
                        ProvisionProductDryRunTask(**provisioning_parameters)
                    )
                else:
                    provisions.append(
                        RunDeployInSpokeTask(**run_deploy_in_spoke_task_params)
                    )

            elif task_status == constants.TERMINATED:
                terminating_parameters = {}
                for p in TerminateProductTask.get_param_names(include_significant=True):
                    terminating_parameters[p] = task_def.get(p)

                if self.is_dry_run:
                    provisions.append(
                        TerminateProductDryRunTask(**terminating_parameters)
                    )
                else:
                    provisions.append(
                        RunDeployInSpokeTask(**run_deploy_in_spoke_task_params)
                    )
            else:
                raise Exception(f"Unsupported status of {task_status}")
        self.info(f"len of provisions: {len(provisions)}")
        return provisions

    def requires(self):
        configuration = manifest_utils_for_launches.get_configuration_from_launch(
            self.manifest, self.launch_name
        )
        configuration["single_account"] = self.single_account
        configuration["is_dry_run"] = self.is_dry_run
        configuration["puppet_account_id"] = self.puppet_account_id
        configuration["should_use_sns"] = self.should_use_sns
        configuration["should_use_product_plans"] = self.should_use_product_plans

        launch_tasks_def = self.manifest.get_task_defs_from_details(
            self.puppet_account_id, False, self.launch_name, configuration, "launches"
        )
        requirements = dict(
            launches=self.generate_tasks(launch_tasks_def, self.manifest)
        )
        return requirements

    def run(self):
        self.info("started")
        self.write_output(self.params_for_results_display())


class LaunchTask(ProvisioningTask, manifest_tasks.ManifestMixen):
    launch_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()
    execution_mode = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "launch_name": self.launch_name,
            "execution_mode": self.execution_mode,
            "cache_invalidator": self.cache_invalidator,
        }

    def generate_provisions(self, task_defs, manifest):
        self.info("generate_provisions")
        provisions = []
        accounts_by_id = dict()
        for a in manifest.get("accounts"):
            accounts_by_id[a.get("account_id")] = a

        version_details = self.input().get("version_details")

        for task_def in task_defs:
            if self.single_account == "None" or self.single_account is None:
                pass
            else:
                if task_def.get("account_id") != self.single_account:
                    continue
            task_status = task_def.get("status")
            del task_def["status"]
            del task_def["depends_on"]
            task_def["is_dry_run"] = self.is_dry_run

            puppet_account_id = task_def.get("puppet_account_id")
            portfolio = task_def.get("portfolio")
            product = task_def.get("product")
            version = task_def.get("version")
            account_id = task_def.get("account_id")
            region = task_def.get("region")

            d = json.loads(
                version_details[
                    "_".join(
                        [
                            str(puppet_account_id),
                            portfolio,
                            product,
                            version,
                            str(account_id),
                            region,
                        ]
                    )
                ]
                .open("r")
                .read()
            )

            version_id = d.get("version_details").get("version_id")

            product_id = d.get("product_details").get("product_id")

            portfolio_id = d.get("portfolio_details").get("portfolio_id")

            if task_status == constants.PROVISIONED:
                provisioning_parameters = dict()

                for p in ProvisionProductTask.get_param_names(include_significant=True):
                    provisioning_parameters[p] = task_def.get(p)

                provisioning_parameters.update(
                    dict(
                        version_id=version_id,
                        product_id=product_id,
                        portfolio_id=portfolio_id,
                        cache_invalidator=self.cache_invalidator,
                        manifest_file_path=self.manifest_file_path,
                    )
                )

                if self.is_dry_run:
                    provisions.append(
                        ProvisionProductDryRunTask(**provisioning_parameters)
                    )
                else:
                    provisions.append(ProvisionProductTask(**provisioning_parameters))

            elif task_status == constants.TERMINATED:
                terminating_parameters = dict()
                for p in TerminateProductTask.get_param_names(include_significant=True):
                    terminating_parameters[p] = task_def.get(p)

                    terminating_parameters.update(
                        dict(
                            version_id=version_id,
                            product_id=product_id,
                            portfolio_id=portfolio_id,
                            cache_invalidator=self.cache_invalidator,
                            manifest_file_path=self.manifest_file_path,
                        )
                    )

                if self.is_dry_run:
                    provisions.append(
                        TerminateProductDryRunTask(**terminating_parameters)
                    )
                else:
                    provisions.append(TerminateProductTask(**terminating_parameters))
            else:
                raise Exception(f"Unsupported status of {task_status}")
        return provisions

    def requires(self):
        launch = self.manifest.get("launches", {}).get(self.launch_name)

        if not launch:
            raise Exception(self.launch_name)

        dependencies = list()
        version_details = dict()
        requirements = dict(
            dependencies=dependencies,
            version_details=version_details,
            generate_shares=generate_tasks.GenerateSharesTask(
                puppet_account_id=self.puppet_account_id,
                manifest_file_path=self.manifest_file_path,
                should_use_sns=self.should_use_sns,
                section=constants.LAUNCHES,
                cache_invalidator=self.cache_invalidator,
            ),
        )

        for dependency in launch.get("depends_on", []):
            if isinstance(dependency, str):
                dependencies.append(
                    self.__class__(
                        launch_name=dependency,
                        manifest_file_path=self.manifest_file_path,
                        puppet_account_id=self.puppet_account_id,
                        should_use_sns=self.should_use_sns,
                        should_use_product_plans=self.should_use_product_plans,
                        include_expanded_from=self.include_expanded_from,
                        single_account=self.single_account,
                        is_dry_run=self.is_dry_run,
                        execution_mode=self.execution_mode,
                        cache_invalidator=self.cache_invalidator,
                    )
                )
            else:
                dependency_type = dependency.get("type", "launch")
                if dependency_type == "launch":
                    dependencies.append(
                        self.__class__(
                            launch_name=dependency,
                            manifest_file_path=self.manifest_file_path,
                            puppet_account_id=self.puppet_account_id,
                            should_use_sns=self.should_use_sns,
                            should_use_product_plans=self.should_use_product_plans,
                            include_expanded_from=self.include_expanded_from,
                            single_account=self.single_account,
                            is_dry_run=self.is_dry_run,
                            execution_mode=self.execution_mode,
                            cache_invalidator=self.cache_invalidator,
                        )
                    )
                elif dependency_type == "lambda-invocation":
                    from servicecatalog_puppet.workflow.lambda_invocations import (
                        LambdaInvocationTask,
                    )

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

        launch_tasks_defs = self.get_launch_tasks_defs()
        for task_def in launch_tasks_defs:
            if self.single_account == "None" or self.single_account is None:
                pass
            else:
                if task_def.get("account_id") != self.single_account:
                    continue

            puppet_account_id = task_def.get("puppet_account_id")
            portfolio = task_def.get("portfolio")
            product = task_def.get("product")
            version = task_def.get("version")
            account_id = task_def.get("account_id")
            region = task_def.get("region")

            version_details[
                "_".join(
                    [
                        str(puppet_account_id),
                        portfolio,
                        product,
                        version,
                        str(account_id),
                        region,
                    ]
                )
            ] = portfoliomanagement_tasks.GetVersionDetailsByNames(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=puppet_account_id,
                portfolio=portfolio,
                product=product,
                version=version,
                account_id=puppet_account_id,
                region=region,
                cache_invalidator=self.cache_invalidator,
            )

        return requirements

    @lru_cache()
    def get_launch_tasks_defs(self):
        launch = self.manifest.get("launches").get(self.launch_name)
        if not launch:
            raise Exception(self.launch_name)

        configuration = manifest_utils_for_launches.get_configuration_from_launch(
            self.manifest, self.launch_name
        )
        configuration["single_account"] = self.single_account
        configuration["is_dry_run"] = self.is_dry_run
        configuration["puppet_account_id"] = self.puppet_account_id
        configuration["should_use_sns"] = self.should_use_sns
        configuration["should_use_product_plans"] = self.should_use_product_plans

        configuration["execution"] = launch.get("execution")

        launch_tasks_def = self.manifest.get_task_defs_from_details(
            self.puppet_account_id, False, self.launch_name, configuration, "launches"
        )
        return launch_tasks_def

    def run(self):
        self.info("started")
        launch_tasks_def = self.get_launch_tasks_defs()

        self.info(f"{self.uid} starting pre actions")
        pre_actions = self.manifest.get_actions_from(
            self.launch_name, "pre", "launches"
        )
        yield [
            portfoliomanagement_tasks.ProvisionActionTask(
                self.manifest_file_path,
                **p,
                puppet_account_id=self.puppet_account_id,
                cache_invalidator=self.cache_invalidator,
            )
            for p in pre_actions
        ]
        self.info(f"{self.uid} finished pre actions")

        self.info(f"{self.uid} starting launches")
        ls = self.generate_provisions(launch_tasks_def, self.manifest)
        yield ls
        self.info(f"{self.uid} finished launches")

        self.info(f"{self.uid} starting post actions")
        post_actions = self.manifest.get_actions_from(
            self.launch_name, "post", "launches"
        )
        yield [
            portfoliomanagement_tasks.ProvisionActionTask(
                self.manifest_file_path,
                **p,
                puppet_account_id=self.puppet_account_id,
                cache_invalidator=self.cache_invalidator,
            )
            for p in post_actions
        ]
        self.info(f"{self.uid} finished post actions")

        self.write_output(dict(**self.params_for_results_display(), skipped=False))
        self.info("Finished")


class SpokeLocalPortfolioTask(ProvisioningTask, manifest_tasks.ManifestMixen):
    spoke_local_portfolio_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()
    should_use_sns = luigi.BoolParameter()
    should_use_product_plans = luigi.BoolParameter()
    include_expanded_from = luigi.BoolParameter()
    single_account = luigi.Parameter()
    is_dry_run = luigi.BoolParameter()
    depends_on = luigi.ListParameter()
    sharing_mode = luigi.Parameter()
    cache_invalidator = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "sharing_mode": self.sharing_mode,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        self.info("requires")
        dependencies = [
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
            for dependency in self.depends_on
        ]
        self.info(f"dependencies are {dependencies}")

        task_defs = self.get_task_defs()
        portfolio_ids = dict()

        self.info("requires:about to iter")
        for task_def in task_defs:
            # if task_def.get("status") == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED:  # Dodgy if
            portfolio_ids[
                "_".join(
                    [
                        str(self.puppet_account_id),
                        task_def.get("portfolio"),
                        str(task_def.get("account_id")),
                        task_def.get("region"),
                    ]
                )
            ] = portfoliomanagement_tasks.GetPortfolioByPortfolioName(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=task_def.get("portfolio"),
                account_id=self.puppet_account_id,
                region=task_def.get("region"),
                cache_invalidator=self.cache_invalidator,
            )

        self.info("requires:about to return")
        return dict(dependencies=dependencies, portfolio_ids=portfolio_ids,)

    def generate_tasks(self, task_defs):
        self.info("generate_tasks in")
        if len(task_defs) == 0:
            self.warning(
                f"The configuration for this share does not include any target accounts: {self.spoke_local_portfolio_name}"
            )
            return []
        first_task_def = task_defs[0]
        # portfolio = first_task_def.get("portfolio")
        tasks = []
        portfolio_ids = self.input().get("portfolio_ids")

        for task_def in task_defs:
            self.info("generate_tasks main loop iteration 1")
            p = (
                portfolio_ids[
                    "_".join(
                        [
                            str(self.puppet_account_id),
                            task_def.get("portfolio"),
                            str(task_def.get("account_id")),
                            task_def.get("region"),
                        ]
                    )
                ]
                .open("r")
                .read()
            )
            p = json.loads(p)
            portfolio_id = p.get("portfolio_id")

            product_generation_method = task_def.get(
                "product_generation_method", "copy"
            )

            sharing_mode = task_def.get("sharing_mode", constants.SHARING_MODE_DEFAULT)

            self.info("generate_tasks main loop iteration 2")
            if (
                task_def.get("status")
                == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_TERMINATED
            ):
                tasks.append(
                    portfoliomanagement_tasks.DeletePortfolio(
                        manifest_file_path=self.manifest_file_path,
                        account_id=task_def.get("account_id"),
                        region=task_def.get("region"),
                        portfolio=task_def.get("portfolio"),
                        product_generation_method=product_generation_method,
                        puppet_account_id=task_def.get("puppet_account_id"),
                    )
                )
            elif (
                task_def.get("status") == constants.SPOKE_LOCAL_PORTFOLIO_STATUS_SHARED
            ):

                create_spoke_local_portfolio_task_params = dict(
                    manifest_file_path=self.manifest_file_path,
                    puppet_account_id=self.puppet_account_id,
                    account_id=task_def.get("account_id"),
                    region=task_def.get("region"),
                    portfolio=task_def.get("portfolio"),
                    organization=task_def.get("organization"),
                    portfolio_id=portfolio_id,
                    sharing_mode=sharing_mode,
                    cache_invalidator=self.cache_invalidator,
                )

                create_spoke_local_portfolio_task = portfoliomanagement_tasks.CreateSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_params
                )
                tasks.append(create_spoke_local_portfolio_task)

            create_spoke_local_portfolio_task_as_dependency_params = dict(
                manifest_file_path=self.manifest_file_path,
                account_id=task_def.get("account_id"),
                region=task_def.get("region"),
                portfolio=task_def.get("portfolio"),
                organization=task_def.get("organization"),
                portfolio_id=portfolio_id,
            )

            if len(task_def.get("associations", [])) > 0:
                create_associations_for_portfolio_task = portfoliomanagement_tasks.CreateAssociationsForPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    sharing_mode=sharing_mode,
                    cache_invalidator=self.cache_invalidator,
                    associations=task_def.get("associations"),
                    puppet_account_id=task_def.get("puppet_account_id"),
                    should_use_sns=task_def.get("should_use_sns"),
                )
                tasks.append(create_associations_for_portfolio_task)

            launch_constraints = task_def.get("constraints", {}).get("launch", [])

            if product_generation_method == "import":
                import_into_spoke_local_portfolio_task = portfoliomanagement_tasks.ImportIntoSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    sharing_mode=sharing_mode,
                    cache_invalidator=self.cache_invalidator,
                    puppet_account_id=task_def.get("puppet_account_id"),
                )
                tasks.append(import_into_spoke_local_portfolio_task)
            else:
                copy_into_spoke_local_portfolio_task = portfoliomanagement_tasks.CopyIntoSpokeLocalPortfolioTask(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    sharing_mode=sharing_mode,
                    cache_invalidator=self.cache_invalidator,
                    puppet_account_id=task_def.get("puppet_account_id"),
                )
                tasks.append(copy_into_spoke_local_portfolio_task)

            if len(launch_constraints) > 0:
                create_launch_role_constraints_for_portfolio_task_params = {
                    "launch_constraints": launch_constraints,
                    "puppet_account_id": task_def.get("puppet_account_id"),
                    "should_use_sns": task_def.get("should_use_sns"),
                }
                create_launch_role_constraints_for_portfolio = portfoliomanagement_tasks.CreateLaunchRoleConstraintsForPortfolio(
                    **create_spoke_local_portfolio_task_as_dependency_params,
                    **create_launch_role_constraints_for_portfolio_task_params,
                    sharing_mode=sharing_mode,
                    cache_invalidator=self.cache_invalidator,
                    product_generation_method=product_generation_method,
                )
                tasks.append(create_launch_role_constraints_for_portfolio)
        self.info(f"tasks len are {len(tasks)}")
        self.info("generate_tasks out")
        return tasks

    @lru_cache()
    def get_task_defs(self):
        self.info("get_task_defs in")
        spoke_local_portfolio_details = self.manifest.get("spoke-local-portfolios").get(
            self.spoke_local_portfolio_name
        )
        configuration = {
            "spoke_local_portfolio_name": self.spoke_local_portfolio_name,
            "status": spoke_local_portfolio_details.get("status", "shared"),
            "portfolio": spoke_local_portfolio_details.get("portfolio"),
            "associations": spoke_local_portfolio_details.get("associations", []),
            "constraints": spoke_local_portfolio_details.get("constraints", {}),
            "depends_on": spoke_local_portfolio_details.get("depends_on", []),
            "retry_count": spoke_local_portfolio_details.get("retry_count", 1),
            "requested_priority": spoke_local_portfolio_details.get(
                "requested_priority", 0
            ),
            "worker_timeout": spoke_local_portfolio_details.get(
                "timeoutInSeconds", constants.DEFAULT_TIMEOUT
            ),
            "product_generation_method": spoke_local_portfolio_details.get(
                "product_generation_method", "copy"
            ),
            "single_account": self.single_account,
            "is_dry_run": self.is_dry_run,
            "puppet_account_id": self.puppet_account_id,
            "should_use_sns": self.should_use_sns,
            "should_use_product_plans": self.should_use_product_plans,
        }
        configuration.update(
            manifest_utils.get_configuration_overrides(
                self.manifest, spoke_local_portfolio_details
            )
        )

        self.info("get_task_defs out")

        return self.manifest.get_task_defs_from_details(
            self.puppet_account_id,
            True,
            self.spoke_local_portfolio_name,
            configuration,
            "spoke-local-portfolios",
        )

    def run(self):
        self.info("started")

        task_defs = self.get_task_defs()

        self.info("about to get the pre actions")
        pre_actions = self.manifest.get_actions_from(
            self.spoke_local_portfolio_name, "pre", "spoke-local-portfolios"
        )
        self.info("about to get the post actions")
        post_actions = self.manifest.get_actions_from(
            self.spoke_local_portfolio_name, "post", "spoke-local-portfolios"
        )

        self.info(f"starting pre actions")
        yield [
            portfoliomanagement_tasks.ProvisionActionTask(
                **p,
                puppet_account_id=self.puppet_account_id,
                cache_invalidator=self.cache_invalidator,
            )
            for p in pre_actions
        ]
        self.info(f"finished pre actions")

        self.info(f"starting launches")
        yield self.generate_tasks(task_defs)
        self.info(f"{self.uid} finished launches")

        self.info(f"{self.uid} starting post actions")
        yield [
            portfoliomanagement_tasks.ProvisionActionTask(
                **p,
                puppet_account_id=self.puppet_account_id,
                cache_invalidator=self.cache_invalidator,
            )
            for p in post_actions
        ]
        self.info(f"{self.uid} finished post actions")

        self.write_output(self.params_for_results_display())
        self.info("finished")
