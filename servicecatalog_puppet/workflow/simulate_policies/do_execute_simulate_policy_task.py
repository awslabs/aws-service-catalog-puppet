#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi
import yaml

from servicecatalog_puppet.workflow import dependency
from servicecatalog_puppet.workflow.simulate_policies import simulate_policy_base_task
from servicecatalog_puppet.workflow.manifest import manifest_mixin


class DoExecuteSimulatePolicyTask(
    simulate_policy_base_task.SimulatePolicyBaseTask,
    manifest_mixin.ManifestMixen,
    dependency.DependenciesMixin,
):
    simulate_policy_name = luigi.Parameter()
    puppet_account_id = luigi.Parameter()

    region = luigi.Parameter()
    account_id = luigi.Parameter()

    execution = luigi.Parameter()

    requested_priority = luigi.IntParameter()

    simulation_type = luigi.Parameter()
    policy_source_arn = luigi.Parameter()
    policy_input_list = luigi.ListParameter()
    permissions_boundary_policy_input_list = luigi.ListParameter()
    action_names = luigi.ListParameter()
    expected_decision = luigi.Parameter()
    resource_arns = luigi.ListParameter()
    resource_policy = luigi.Parameter()
    resource_owner = luigi.Parameter()
    caller_arn = luigi.Parameter()
    context_entries = luigi.ListParameter()
    resource_handling_option = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "puppet_account_id": self.puppet_account_id,
            "simulate_policy_name": self.simulate_policy_name,
            "region": self.region,
            "account_id": self.account_id,
            "cache_invalidator": self.cache_invalidator,
        }

    def api_calls_used(self):
        return [
            f"iam.simulate_{self.simulation_type}_policy_{self.account_id}_{self.region}"
        ]

    def run(self):
        with self.spoke_regional_client("iam") as iam:
            kwargs = dict(ActionNames=self.action_names)
            if len(self.policy_input_list) > 0:
                kwargs["PolicyInputList"] = self.policy_input_list

            if len(self.permissions_boundary_policy_input_list) > 0:
                kwargs[
                    "PermissionsBoundaryPolicyInputList"
                ] = self.permissions_boundary_policy_input_list

            if len(self.resource_arns) > 0:
                kwargs["ResourceArns"] = self.resource_arns

            if self.resource_policy != "":
                kwargs["ResourcePolicy"] = self.resource_policy

            if self.resource_owner != "":
                kwargs["ResourceOwner"] = self.resource_owner

            if self.caller_arn != "":
                kwargs["CallerArn"] = self.caller_arn

            if len(self.context_entries) > 0:
                kwargs["ContextEntries"] = self.context_entries

            if self.resource_handling_option != "":
                kwargs["ResourceHandlingOption"] = self.resource_handling_option

            if self.simulation_type == "principal":
                kwargs["PolicySourceArn"] = self.policy_source_arn.replace(
                    "${AWS::AccountId}", self.account_id
                )
                result = iam.simulate_principal_policy(**kwargs)
            else:
                if len(self.policy_input_list) == 0:
                    raise Exception(
                        "policy_input_list is required when simulation_type is 'custom'"
                    )
                result = iam.simulate_custom_policy(**kwargs)

            failures = list()
            for evaluation_result in result.get("EvaluationResults"):
                if evaluation_result.get("EvalDecision") != self.expected_decision:
                    failures.append(evaluation_result)

            if len(failures) > 0:
                raise Exception(
                    f"{len(failures)} unexpected decision(s) encountered:\n{yaml.safe_dump(failures)}"
                )

        self.write_output(result)
