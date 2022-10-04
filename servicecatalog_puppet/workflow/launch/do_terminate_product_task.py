#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import time

import luigi

from servicecatalog_puppet import serialisation_utils
from servicecatalog_puppet.workflow.dependencies import tasks


class DoTerminateProductTask(tasks.TaskWithReference):
    launch_name = luigi.Parameter()

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

    def run(self):
        with self.spoke_regional_client("servicecatalog") as service_catalog:
            try:
                service_catalog.describe_provisioned_product(Name=self.launch_name)
            except service_catalog.exceptions.ResourceNotFoundException:
                self.write_empty_output()
                return

            record_detail = service_catalog.terminate_provisioned_product(
                ProvisionedProductName=self.launch_name
            ).get("RecordDetail")
            record_id = record_detail.get("RecordId")

            status = "IN_PROGRESS"
            while status == "IN_PROGRESS":
                record_detail = service_catalog.describe_record(Id=record_id).get(
                    "RecordDetail"
                )
                status = record_detail.get("Status")
                self.info(f"termination of {self.launch_name} current status: {status}")
                if status != "IN_PROGRESS":
                    break
                else:
                    time.sleep(3)

            if status not in ["CREATED", "SUCCEEDED"]:
                self.info(serialisation_utils.dump(record_detail.get("RecordErrors")))
                raise Exception(
                    f"Failed to terminate provisioned product: Status = {status}"
                )

            self.write_empty_output()
