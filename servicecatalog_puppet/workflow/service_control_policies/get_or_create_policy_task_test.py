#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import io
import json
import unittest

from servicecatalog_puppet import serialisation_utils

from botocore.response import StreamingBody

from servicecatalog_puppet.workflow import tasks_unit_tests_helper


class GetOrCreatePolicyTaskTest(tasks_unit_tests_helper.PuppetTaskUnitTest):
    service_control_policy_name = "service_control_policy_name"
    puppet_account_id = "puppet_account_id"
    manifest_file_path = "manifest_file_path"
    manifest_task_reference_file_path = "manifest_task_reference_file_path"
    task_reference = "task_reference"
    dependencies_by_reference = []
    account_id = "account_id"
    manifest_file_path = "manifest_file_path"

    def setUp(self) -> None:
        from servicecatalog_puppet.workflow.service_control_policies import (
            get_or_create_policy_task,
        )

        self.module = get_or_create_policy_task

        self.policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": ["organizations:LeaveOrganization"],
                    "Resource": "*",
                }
            ],
        }

        self.sut = self.module.GetOrCreatePolicyTask(
            **self.get_common_args(),
            account_id=self.account_id,
            region="us-east-1",
            policy_name="my_policy",
            policy_description="my description",
            policy_content=dict(default=self.policy),
            manifest_file_path=self.manifest_file_path,
            tags=[],
        )

        self.wire_up_mocks()

    def test_get_policy_content_inline(self):
        # setup
        expected_result = self.policy

        # exercise
        actual_result = self.sut.get_unwrapped_policy()

        # verify
        self.assertEqual(expected_result, actual_result)

    @unittest.skip
    def test_get_policy_content_s3(self):
        # setup
        expected_result = self.policy
        self.sut.policy_content = dict(s3=dict(bucket="my_bucket", key="my_key"))

        encoded_policy = json.dumps(self.policy).encode("utf-8")
        self.hub_client_mock.get_object.return_value = {
            "Body": StreamingBody(io.BytesIO(encoded_policy), len(encoded_policy))
        }

        # exercise
        actual_result = self.sut.get_unwrapped_policy()

        # verify
        self.assertEqual(expected_result, actual_result)

    def test_get_policy_content_unsupported(self):
        # setup
        expected_result = self.policy
        self.sut.policy_content = dict(invalid=None)

        # exercise
        with self.assertRaises(Exception) as ex:
            self.sut.get_unwrapped_policy()

        # verify
        self.assertTrue("Not supported policy content structure" in str(ex.exception))
