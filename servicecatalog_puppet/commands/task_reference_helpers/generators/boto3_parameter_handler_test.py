#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import unittest

from servicecatalog_puppet import constants, task_reference_constants


class Boto3ParameterHandlerTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        from servicecatalog_puppet.commands.task_reference_helpers.generators import (
            boto3_parameter_handler,
        )

        self.sut = boto3_parameter_handler

    def test_for_boto3_parameters(self):
        # setup
        puppet_account_id = "hub_account_id"
        account_id = "spoke_account_id"
        region = "eu-west-0"
        item_name = "depsrefactor"
        dependency_item_name = "something_else"

        section_name = constants.STACKS
        task = {
            "stack_name": item_name,
            "launch_name": "",
            "stack_set_name": "",
            "capabilities": ["CAPABILITY_NAMED_IAM"],
            "ssm_param_outputs": [],
            "bucket": f"sc-puppet-stacks-repository-{puppet_account_id}",
            "key": f"stack/{item_name}/v1/stack.template-${{AWS::Region}}.yaml",
            "version_id": "",
            "execution": "spoke",
            "use_service_role": True,
            "tags": [],
            "puppet_account_id": puppet_account_id,
            "status": None,
            "requested_priority": 0,
            "dependencies": [
                {"affinity": "stack", "name": dependency_item_name, "type": "stack",}
            ],
            "account_id": account_id,
            "region": region,
            task_reference_constants.MANIFEST_SECTION_NAMES: {"stacks": True},
            task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
            task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
            "section_name": "stacks",
            "item_name": item_name,
            "dependencies_by_reference": [
                "create-policies",
                f"prepare-account-for-stacks-{account_id}",
                f"get-template-from-s3-stacks-{item_name}",
            ],
            "task_reference": f"stacks_ccoe-{item_name}_{account_id}_{region}",
            "get_s3_template_ref": f"get-template-from-s3-stacks-{item_name}",
        }
        task_reference = task["task_reference"]
        new_tasks = {task_reference: task}

        describe_stacks_filter = "xyz"

        output_key = "SomeOutputKey"

        parameter_details = {
            "boto3": {
                "account_id": "${AWS::AccountId}",
                "arguments": {"StackName": item_name},
                "call": "describe_stacks",
                "client": "cloudformation",
                "filter": describe_stacks_filter,
                "region": "${AWS::Region}",
                "use_paginator": True,
            },
            "cloudformation_stack_output": {
                "account_id": "${AWS::AccountId}",
                "output_key": output_key,
                "region": "${AWS::Region}",
                "stack_name": dependency_item_name,
            },
        }

        parameter_name = "some_parameter"

        # exercise
        self.sut.boto3_parameter_handler(
            new_tasks, parameter_details, parameter_name, puppet_account_id, task,
        )

        # verify
        n_new_tasks = len(new_tasks.keys())
        boto3_parameter_task_reference = f"{constants.BOTO3_PARAMETERS}-cloudformation_stack_output-{dependency_item_name}-{output_key}-{account_id}-{region}"
        self.assertEqual(
            [
                "create-policies",
                f"prepare-account-for-stacks-{account_id}",
                f"get-template-from-s3-stacks-{item_name}",
                boto3_parameter_task_reference,
            ],
            new_tasks[task_reference].get("dependencies_by_reference"),
            "assert new dependency is added to the task needing the parameter",
        )

        expected_boto3_task_ref = f"{constants.BOTO3_PARAMETERS}-{section_name}-{item_name}-{parameter_name}-{account_id}-{region}"
        self.assertEqual(
            {
                "status": None,
                "execution": "spoke",
                "task_reference": boto3_parameter_task_reference,
                "dependencies_by_reference": [],
                "dependencies": [],
                task_reference_constants.MANIFEST_SECTION_NAMES: {
                    constants.STACKS: True
                },
                task_reference_constants.MANIFEST_ITEM_NAMES: {item_name: True},
                task_reference_constants.MANIFEST_ACCOUNT_IDS: {account_id: True},
                "account_id": account_id,
                "region": region,
                "arguments": {"StackName": item_name},
                "call": "describe_stacks",
                "client": "cloudformation",
                "filter": describe_stacks_filter,
                "use_paginator": True,
                "section_name": constants.BOTO3_PARAMETERS,
            },
            new_tasks[boto3_parameter_task_reference],
            "assert the boto3 task is generated correctly",
        )

        self.assertEqual(2, n_new_tasks, "assert the correct number of tasks exist")
