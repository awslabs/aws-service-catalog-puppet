# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from unittest import mock

from pytest import fixture
import json

from servicecatalog_puppet import constants, luigi_tasks_and_targets


@fixture
def sut():
    from servicecatalog_puppet import cli_commands
    return cli_commands


def test_dry_run(sut, mocker):
    # setup
    f = mock.MagicMock()
    mocked_manifest = mock.MagicMock()
    mocked_manifest_utils = mocker.patch.object(sut, 'manifest_utils')
    mocked_manifest_utils.load.return_value = mocked_manifest
    mocked_cli_command_helpers = mocker.patch.object(sut, 'cli_command_helpers')
    all_launch_tasks = {}
    mocked_cli_command_helpers.deploy_launches.return_value = all_launch_tasks
    provision_task_args = {
        "status": constants.PROVISIONED,
        "launch_name": "",
        "portfolio": "",
        "product": "",
        "version": "",
        "product_id": "",
        "version_id": "",
        "account_id": "",
        "region": "",
        "puppet_account_id": "",
        "dependencies": (),
        "parameters": (),
        "retry_count": 1,
        "ssm_param_inputs": (),
        "ssm_param_outputs": (),
        "worker_timeout": 2,
    }
    terminate_task_args = {
        "status": constants.TERMINATED,
        "launch_name": "",
        "portfolio": "",
        "product": "",
        "version": "",
        "product_id": "",
        "version_id": "",
        "account_id": "",
        "region": "",
        "puppet_account_id": "",
        "retry_count": 1,
        "ssm_param_outputs": [],
        "worker_timeout": 2,
    }
    mocked_cli_command_helpers.wire_dependencies.return_value = [
        provision_task_args,
        terminate_task_args,
    ]

    # exercise
    sut.dry_run(f)

    # assert
    mocked_manifest_utils.load.assert_called_once_with(f)
    mocked_cli_command_helpers.deploy_launches.assert_called_with(mocked_manifest)
    mocked_cli_command_helpers.wire_dependencies.assert_called_with(all_launch_tasks)
    assert mocked_cli_command_helpers.run_tasks_for_dry_run.call_count == 1
    args, kwargs = mocked_cli_command_helpers.run_tasks_for_dry_run.call_args
    assert len(args[0]) == 2
    assert isinstance(args[0][0], luigi_tasks_and_targets.ProvisionProductDryRunTask)
    assert isinstance(args[0][1], luigi_tasks_and_targets.TerminateProductDryRunTask)
