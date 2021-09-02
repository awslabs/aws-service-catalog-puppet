#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.launch import provisioning_artifact_parameters_task
from servicecatalog_puppet.workflow.launch import provisioning_task
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_version_details_by_names_task,
)


class ProvisionProductTask(
    provisioning_task.ProvisioningTask, dependency.DependenciesMixin
):
    launch_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    execution = luigi.Parameter()

    try_count = 1

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "launch_name": self.launch_name,
            "account_id": self.account_id,
            "region": self.region,
            "cache_invalidator": self.cache_invalidator,
        }

    @property
    def priority(self):
        return self.requested_priority

    def requires(self):
        requirements = {
            "section_dependencies": self.get_section_dependencies(),
            "ssm_params": self.get_parameters_tasks(),
            "provisioning_artifact_parameters": provisioning_artifact_parameters_task.ProvisioningArtifactParametersTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                product=self.product,
                version=self.version,
                region=self.region,
            ),
            "details": get_version_details_by_names_task.GetVersionDetailsByNames(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.single_account
                if self.execution_mode == constants.EXECUTION_MODE_SPOKE
                else self.puppet_account_id,
                portfolio=self.portfolio,
                product=self.product,
                version=self.version,
                region=self.region,
            ),
        }
        return requirements

    def api_calls_used(self):
        apis = [
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
        ]
        if self.should_use_product_plans:
            apis.append(
                f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            )
        return apis

    def run(self):
        details = self.load_from_input("details")
        product_id = details.get("product_details").get("ProductId")
        version_id = details.get("version_details").get("Id")

        task_output = dict(
            **self.params_for_results_display(),
            account_parameters=tasks.unwrap(self.account_parameters),
            launch_parameters=tasks.unwrap(self.launch_parameters),
            manifest_parameters=tasks.unwrap(self.manifest_parameters),
        )

        all_params = self.get_parameter_values()

        with self.spoke_regional_client("servicecatalog") as service_catalog:
            path_name = self.portfolio

            (
                provisioned_product_id,
                provisioning_artifact_id,
                provisioned_product_status,
            ) = aws.terminate_if_status_is_not_available(
                service_catalog,
                self.launch_name,
                product_id,
                self.account_id,
                self.region,
                self.should_delete_rollback_complete_stacks,
            )
            self.info(
                f"pp_id: {provisioned_product_id}, paid : {provisioning_artifact_id}"
            )

            with self.spoke_regional_client("cloudformation") as cloudformation:
                need_to_provision = True

                self.info(
                    f"running ,checking {product_id} {version_id} {path_name} in {self.account_id} {self.region}"
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

                if provisioning_artifact_id == version_id:
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

                if provisioned_product_status == "TAINTED":
                    need_to_provision = True

                if need_to_provision:
                    self.info(
                        f"about to provision with params: {json.dumps(tasks.unwrap(params_to_use))}"
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
                            path_id = aws.get_path_for_product(
                                service_catalog, product_id, self.portfolio
                            )
                            provisioned_product_id = aws.provision_product_with_plan(
                                service_catalog,
                                self.launch_name,
                                self.account_id,
                                self.region,
                                product_id,
                                version_id,
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
                                product_id,
                                version_id,
                                self.puppet_account_id,
                                path_name,
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
                            product_id,
                            version_id,
                            self.puppet_account_id,
                            path_name,
                            params_to_use,
                            self.version,
                            self.should_use_sns,
                            self.execution,
                        )

                self.info(f"self.execution is {self.execution}")
                if self.execution == constants.EXECUTION_MODE_HUB:
                    self.info(
                        f"Running in execution mode: {self.execution}, checking for SSM outputs"
                    )
                    with self.spoke_regional_client(
                        "cloudformation"
                    ) as spoke_cloudformation:
                        stack_details = aws.get_stack_output_for(
                            spoke_cloudformation,
                            f"SC-{self.account_id}-{provisioned_product_id}",
                        )

                    for ssm_param_output in self.ssm_param_outputs:
                        self.info(
                            f"writing SSM Param: {ssm_param_output.get('stack_output')}"
                        )
                        with self.hub_client("ssm") as ssm:
                            found_match = False
                            # TODO push into another task
                            for output in stack_details.get("Outputs", []):
                                if output.get("OutputKey") == ssm_param_output.get(
                                    "stack_output"
                                ):
                                    ssm_parameter_name = ssm_param_output.get(
                                        "param_name"
                                    )
                                    ssm_parameter_name = ssm_parameter_name.replace(
                                        "${AWS::Region}", self.region
                                    )
                                    ssm_parameter_name = ssm_parameter_name.replace(
                                        "${AWS::AccountId}", self.account_id
                                    )
                                    found_match = True
                                    self.info(f"found value")
                                    ssm.put_parameter_and_wait(
                                        Name=ssm_parameter_name,
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
