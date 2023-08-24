#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0

import unittest
from servicecatalog_puppet import constants, task_reference_constants


class TestCompleteGeneratorSteps(unittest.TestCase):
    def setUp(self):
        from servicecatalog_puppet.commands.task_reference_helpers import (
            complete_generator,
        )

        self.module = complete_generator
        self.sut = complete_generator.set_dependencies_for_ssm_tasks

    def test_ssm_outputs_and_parameters_are_configured_correctly(self):
        # setup
        parameter_name = "foo"
        output_task_account_id = "output_task_account_id"
        generating_output_task_account_id = "generating_output_task_account_id"
        parameter_task_account_id = "parameter_task_account_id"
        consuming_parameter_task_account_id = "consuming_parameter_task_account_id"

        # setup simple objects
        generating_output_task_reference = "generating_output_task_reference"
        generating_output_task = {
            "task_reference": generating_output_task_reference,
            "dependencies_by_reference": [],
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            "account_id": generating_output_task_account_id,
        }

        output_task_reference = f"{constants.SSM_OUTPUTS}-{parameter_name}"
        output_task = {
            "task_reference": output_task_reference,
            "dependencies_by_reference": [],
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            "account_id": output_task_account_id,
        }

        parameter_task_reference = f"{constants.SSM_PARAMETERS}-{parameter_name}"
        parameter_task = {
            "task_reference": parameter_task_reference,
            "dependencies_by_reference": [],
            task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
            "account_id": parameter_task_account_id,
        }

        consuming_parameter_task_reference = "consuming_parameter_task_reference"
        consuming_parameter_task = {
            "task_reference": consuming_parameter_task_reference,
            "dependencies_by_reference": [generating_output_task_reference],
            "account_id": consuming_parameter_task_account_id,
            task_reference_constants.MANIFEST_ACCOUNT_IDS: {},
        }

        # setup dependencies
        generating_output_task["ssm_outputs_tasks_references"] = {
            parameter_name: output_task_reference
        }
        consuming_parameter_task["ssm_parameters_tasks_references"] = {
            parameter_name: parameter_task_reference
        }

        all_tasks = {
            generating_output_task_reference: generating_output_task,
            consuming_parameter_task_reference: consuming_parameter_task,
            output_task_reference: output_task,
            parameter_task_reference: parameter_task,
        }

        # exercise
        self.sut(all_tasks)

        # verify
        self.assertDictEqual(
            {
                "dependencies_by_reference": [],
                "task_reference": generating_output_task_reference,
                task_reference_constants.MANIFEST_ACCOUNT_IDS: dict(),
                "ssm_outputs_tasks_references": {parameter_name: output_task_reference},
                "account_id": generating_output_task_account_id,
            },
            generating_output_task,
            "assert no changes were made",
        )
        self.assertTrue(
            output_task[task_reference_constants.MANIFEST_ACCOUNT_IDS][
                consuming_parameter_task_account_id
            ],
            "manifest_account_ids was added to",
        )
        self.assertTrue(
            parameter_task[task_reference_constants.MANIFEST_ACCOUNT_IDS][
                consuming_parameter_task_account_id
            ],
            "manifest_account_ids was added to",
        )
        self.assertEqual(
            consuming_parameter_task["dependencies_by_reference"],
            [generating_output_task_reference, output_task_reference],
            "output task reference was added",
        )
