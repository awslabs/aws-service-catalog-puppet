#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

import luigi

from servicecatalog_puppet import constants
from servicecatalog_puppet import config
from servicecatalog_puppet.workflow.general import get_ssm_param_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin
from servicecatalog_puppet.workflow.dependencies.get_dependencies_for_task_reference import (
    get_dependencies_for_task_reference,
)


class DoInvokeLambdaTask(
    get_ssm_param_task.PuppetTaskWithParameters, manifest_mixin.ManifestMixen
):
    lambda_invocation_name = luigi.Parameter()
    region = luigi.Parameter()
    account_id = luigi.Parameter()

    function_name = luigi.Parameter()
    qualifier = luigi.Parameter()
    invocation_type = luigi.Parameter()

    manifest_task_reference_file_path = luigi.Parameter()
    task_reference = luigi.Parameter()
    dependencies_by_reference = luigi.ListParameter()

    puppet_account_id = luigi.Parameter()

    manifest_file_path = luigi.Parameter()

    section_name = constants.LAMBDA_INVOCATIONS

    @property
    def item_name(self):
        return self.lambda_invocation_name

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "lambda_invocation_name": self.lambda_invocation_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def requires(self):
        return dict(
            reference_dependencies=get_dependencies_for_task_reference(
                self.manifest_task_reference_file_path,
                self.task_reference,
                self.puppet_account_id,
            ),
        )

    def api_calls_used(self):
        return {
            f"lambda.invoke_{self.get_account_used()}_{self.region}": 1,
        }

    def run(self):
        home_region = config.get_home_region(self.puppet_account_id)
        with self.hub_regional_client(
            "lambda", region_name=home_region
        ) as lambda_client:
            payload = dict(
                account_id=self.account_id,
                region=self.region,
                parameters=self.get_parameter_values(),
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
