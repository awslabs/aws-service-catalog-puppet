#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi

from servicecatalog_puppet import aws
from servicecatalog_puppet import constants
from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.launch import provisioning_task
from servicecatalog_puppet.workflow.portfolio.accessors import (
    get_version_details_by_names_task,
)


class DoTerminateProductTask(
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

    def requires(self):
        requirements = {
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
        return [
            f"servicecatalog.scan_provisioned_products_single_page{self.account_id}_{self.region}",
            f"servicecatalog.terminate_provisioned_product_{self.account_id}_{self.region}",
            f"servicecatalog.describe_record_{self.account_id}_{self.region}",
            # f"ssm.delete_parameter_{self.region}": 1,
        ]

    def run(self):
        self.info(f"starting terminate try {self.try_count} of {self.retry_count}")
        details = self.load_from_input("details")
        product_id = details.get("product_details").get("ProductId")

        with self.spoke_regional_client("servicecatalog") as service_catalog:
            self.info(
                f"[{self.launch_name}] {self.account_id}:{self.region} :: looking for previous failures"
            )
            provisioned_product_id, provisioning_artifact_id = aws.ensure_is_terminated(
                service_catalog, self.launch_name, product_id
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
                with self.hub_client("ssm") as ssm:
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
