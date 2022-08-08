#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import time

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.launch import provisioning_artifact_parameters_task
from servicecatalog_puppet.workflow.launch import provisioning_task
from servicecatalog_puppet.workflow.portfolio.accessors import (
    describe_product_as_admin_task,
)
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)


class ProvisionProductTask(
    provisioning_task.ProvisioningTask, dependency.DependenciesMixin
):
    task_reference = luigi.Parameter()
    manifest_task_reference_file_path = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

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
        reference_dependencies = get_dependencies_for_task_reference(
            self.manifest_task_reference_file_path,
            self.task_reference,
            self.puppet_account_id,
        )

        requirements = {
            "reference_dependencies": reference_dependencies,
            "provisioning_artifact_parameters": provisioning_artifact_parameters_task.ProvisioningArtifactParametersTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                portfolio=self.portfolio,
                product_name=self.product,
                version_name=self.version,
                region=self.region,
            ),
            "describe_product_as_admin_task": describe_product_as_admin_task.DescribeProductAsAdminTask(
                manifest_file_path=self.manifest_file_path,
                puppet_account_id=self.puppet_account_id,
                account_id=self.single_account
                if self.execution_mode == constants.EXECUTION_MODE_SPOKE
                else self.puppet_account_id,
                product_name=self.product,
                region=self.region,
            ),
        }
        return requirements

    def api_calls_used(self):
        apis = [
            # TODO fix check this list to see if all used
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
        ]
        if self.should_use_product_plans:
            apis.append(
                f"servicecatalog.list_launch_paths_{self.account_id}_{self.region}",
            )

        if len(self.ssm_param_outputs) > 0:
            apis.append(f"ssm.put_parameter_and_wait")

        return apis

    def run(self):
        describe_product_as_admin = self.load_from_input(
            "describe_product_as_admin_task"
        )
        product_id = (
            describe_product_as_admin.get("ProductViewDetail")
            .get("ProductViewSummary")
            .get("ProductId")
        )
        version_id = None
        for provisioning_artifact_summary in describe_product_as_admin.get(
            "ProvisioningArtifactSummaries", []
        ):
            if provisioning_artifact_summary.get("Name") == self.version:
                version_id = provisioning_artifact_summary.get("Id")
        if version_id is None:
            raise Exception(f"Did not find version: {self.version} in: {self.product}")

        task_output = dict(
            **self.params_for_results_display(),
            account_parameters=tasks.unwrap(self.account_parameters),
            launch_parameters=tasks.unwrap(self.launch_parameters),
            manifest_parameters=tasks.unwrap(self.manifest_parameters),
        )

        all_params = self.get_parameter_values()

        with self.spoke_regional_client("servicecatalog") as service_catalog:
            path_name = self.portfolio
            # Get the status
            (
                provisioned_product_detail,
                was_provisioned_before,
            ) = self.check_was_previously_provisioned(service_catalog)

            params_to_use = {}
            provisioned_product_id = False
            provisioning_artifact_parameters = self.load_from_input(
                "provisioning_artifact_parameters"
            )
            for p in provisioning_artifact_parameters:
                param_name = p.get("ParameterKey")
                params_to_use[param_name] = all_params.get(
                    param_name, p.get("DefaultValue")
                )

            if was_provisioned_before:
                (
                    product_id,
                    provisioning_artifact_id,
                    provisioned_product_id,
                ) = self.clean_up_existing_provisioned_product(
                    provisioned_product_detail, service_catalog
                )

                need_to_provision = True

                if provisioning_artifact_id == version_id:
                    self.info(f"found previous good provision")
                    if provisioned_product_id:
                        self.info(f"checking params for diffs")
                        pp_stack_name = aws.get_stack_name_for_pp_id(
                            service_catalog, provisioned_product_id
                        )
                        with self.spoke_regional_client(
                            "cloudformation"
                        ) as cloudformation:
                            provisioned_parameters = aws.get_parameters_for_stack(
                                cloudformation, pp_stack_name,
                            )
                        self.info(f"current params: {provisioned_parameters}")
                        self.info(f"new params: {params_to_use}")

                        if provisioned_parameters == params_to_use:
                            self.info(f"params unchanged")
                            need_to_provision = False
                        else:
                            self.info(f"params changed")
            else:
                need_to_provision = True

            task_output["provisioned"] = need_to_provision
            task_output["section_name"] = self.section_name
            if need_to_provision:
                self.info(
                    f"about to provision with params: {json.dumps(tasks.unwrap(params_to_use))}"
                )

                if provisioned_product_id:
                    pp_stack_name = aws.get_stack_name_for_pp_id(
                        service_catalog, provisioned_product_id
                    )
                    stack = aws.get_stack_output_for(cloudformation, pp_stack_name,)
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
                            f"[{self.uid}] {pp_stack_name} has a status of "
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

                # self.info(f"self.execution is {self.execution}")
                # if self.execution in [
                #     constants.EXECUTION_MODE_HUB,
                #     constants.EXECUTION_MODE_SPOKE,
                # ]:
                #     self.info(
                #         f"Running in execution mode: {self.execution}, checking for SSM outputs"
                #     )
                #     outputs = service_catalog.get_provisioned_product_outputs(
                #         ProvisionedProductId=provisioned_product_id
                #     ).get("Outputs", [])
                #     for ssm_param_output in self.ssm_param_outputs:
                #         self.info(
                #             f"writing SSM Param: {ssm_param_output.get('stack_output')}"
                #         )
                #         with self.hub_client("ssm") as ssm:
                #             found_match = False
                #             # TODO push into another task
                #             for output in outputs:
                #                 if output.get("OutputKey") == ssm_param_output.get(
                #                     "stack_output"
                #                 ):
                #                     ssm_parameter_name = ssm_param_output.get(
                #                         "param_name"
                #                     )
                #                     ssm_parameter_name = ssm_parameter_name.replace(
                #                         "${AWS::Region}", self.region
                #                     )
                #                     ssm_parameter_name = ssm_parameter_name.replace(
                #                         "${AWS::AccountId}", self.account_id
                #                     )
                #                     found_match = True
                #                     self.info(f"found value")
                #                     ssm.put_parameter_and_wait(
                #                         Name=ssm_parameter_name,
                #                         Value=output.get("OutputValue"),
                #                         Type=ssm_param_output.get(
                #                             "param_type", "String"
                #                         ),
                #                         Overwrite=True,
                #                     )
                #             if not found_match:
                #                 raise Exception(
                #                     f"[{self.uid}] Could not find match for {ssm_param_output.get('stack_output')}"
                #                 )

                # self.write_output(task_output)
                # else:

        self.write_output(task_output)
        self.info("finished")

    def clean_up_existing_provisioned_product(
        self, provisioned_product_detail, service_catalog
    ):
        provisioned_product_id = provisioned_product_detail.get("Id")
        provisioning_artifact_id = provisioned_product_detail.get(
            "ProvisioningArtifactId"
        )
        product_id = provisioned_product_detail.get("ProductId")
        # Wait for it to complete what it is doing
        while provisioned_product_detail.get("Status") in [
            "UNDER_CHANGE",
            "PLAN_IN_PROGRESS",
        ]:
            time.sleep(1)
            provisioned_product_detail = service_catalog.describe_provisioned_product(
                Name=self.launch_name
            ).get("ProvisionedProductDetail")
        # Delete it if it is non usable
        if provisioned_product_detail.get("Status") in [
            "ERROR",
        ]:
            record_detail = service_catalog.terminate_provisioned_product(
                ProvisionedProductName=self.launch_name
            ).get("RecordDetail")
            while record_detail.get("Status") in [
                "IN_PROGRESS",
                "IN_PROGRESS_IN_ERROR",
            ]:
                time.sleep(1)
                service_catalog.describe_record(Id=record_detail.get("RecordId"))

            if record_detail.get("Status") in [
                "CREATED",
                "FAILED",
            ]:
                raise Exception(
                    f"Unexpected record detail status: {record_detail.get('Status')}"
                )
            elif record_detail.get("Status") in [
                "SUCCEEDED",
            ]:
                pass
            else:
                raise Exception(
                    f"Unhandled record detail status: {record_detail.get('Status')}"
                )

        elif provisioned_product_detail.get("Status") in [
            "TAINTED",
        ]:
            self.warning(f"Provisioned Product is tainted")
        return product_id, provisioning_artifact_id, provisioned_product_id

    def check_was_previously_provisioned(self, service_catalog):
        was_provisioned_before = True
        try:
            provisioned_product_detail = service_catalog.describe_provisioned_product(
                Name=self.launch_name
            ).get("ProvisionedProductDetail")
        except service_catalog.exceptions.ResourceNotFoundException:
            was_provisioned_before = False
            provisioned_product_detail = None
        return provisioned_product_detail, was_provisioned_before
