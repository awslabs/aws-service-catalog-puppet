#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from servicecatalog_puppet import serialisation_utils
import time

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import tasks
from servicecatalog_puppet.workflow.dependencies import tasks


class ProvisionProductTask(tasks.TaskWithParameters):
    manifest_file_path = luigi.Parameter()
    launch_name = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    portfolio = luigi.Parameter()
    product = luigi.Parameter()
    version = luigi.Parameter()

    portfolio_get_all_products_and_their_versions_ref = luigi.Parameter()
    describe_provisioning_params_ref = luigi.Parameter()

    ssm_param_inputs = luigi.ListParameter(default=[], significant=False)

    launch_parameters = luigi.DictParameter(default={}, significant=False)
    manifest_parameters = luigi.DictParameter(default={}, significant=False)
    account_parameters = luigi.DictParameter(default={}, significant=False)

    retry_count = luigi.IntParameter(default=1, significant=False)
    worker_timeout = luigi.IntParameter(default=0, significant=False)
    ssm_param_outputs = luigi.ListParameter(default=[], significant=False)
    requested_priority = luigi.IntParameter(significant=False, default=0)

    execution = luigi.Parameter()
    tags = luigi.ListParameter()

    section_name = constants.LAUNCHES

    @property
    def item_name(self):
        return self.launch_name

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

    def run(self):
        products_and_their_versions = self.get_output_from_reference_dependency(
            self.portfolio_get_all_products_and_their_versions_ref
        )
        product = products_and_their_versions.get(self.product)
        product_id = product.get("ProductId")
        version_id = product.get("Versions").get(self.version).get("Id")
        describe_provisioning_params = self.get_output_from_reference_dependency(
            self.describe_provisioning_params_ref
        )

        task_output = dict(
            **self.params_for_results_display(),
            account_parameters=tasks.unwrap(self.account_parameters),
            launch_parameters=tasks.unwrap(self.launch_parameters),
            manifest_parameters=tasks.unwrap(self.manifest_parameters),
        )

        all_params = self.get_parameter_values()

        with self.spoke_regional_client("servicecatalog") as service_catalog:
            with self.spoke_regional_client("cloudformation") as cloudformation:
                path_name = self.portfolio
                # Get the status
                (
                    provisioned_product_detail,
                    was_provisioned_before,
                ) = self.check_was_previously_provisioned(service_catalog)

                params_to_use = {}
                provisioned_product_id = False
                # provisioning_artifact_parameters = self.load_from_input(
                #     "provisioning_artifact_parameters"
                # )
                for p in describe_provisioning_params:
                    param_name = p.get("ParameterKey")
                    params_to_use[param_name] = all_params.get(
                        param_name, p.get("DefaultValue")
                    )

                if was_provisioned_before:
                    (
                        ignore_me,
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
                                f"[{self.task_reference}] current cfn stack_status is {stack_status}"
                            )
                        if stack_status == "UPDATE_ROLLBACK_COMPLETE":
                            self.warning(
                                f"{pp_stack_name} has a status of "
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
                                self.tags,
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
                                self.tags,
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
                            self.tags,
                        )

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
