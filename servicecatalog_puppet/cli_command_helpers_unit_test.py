# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pytest import fixture
import json
from servicecatalog_puppet import constants


@fixture
def sut():
    from servicecatalog_puppet import cli_command_helpers
    return cli_command_helpers


def test_wire_dependencies(sut, shared_datadir):
    # setup
    all_tasks = json.loads((shared_datadir / 'account-vending' / 'all-tasks.json').read_text())
    launch_a = json.loads((shared_datadir / 'account-vending' / 'launch-a.json').read_text())
    launch_b = json.loads((shared_datadir / 'account-vending' / 'launch-b.json').read_text())
    launch_c = json.loads((shared_datadir / 'account-vending' / 'launch-c.json').read_text())

    expected_results = [
        launch_a,
        launch_b,
        launch_c
    ]

    # exercise
    actual_results = sut.wire_dependencies(all_tasks)

    # verify
    assert actual_results == expected_results


def test_deploy_launches_task_builder_for_account_launch_region(sut, mocker, shared_datadir):
    # setup
    account_id = '0123456789010'
    deployment_map = json.loads((shared_datadir / 'account-vending' / 'deployment-map.json').read_text())
    launch_details = json.loads((shared_datadir / 'account-vending' / 'launch-details-for-launch-b.json').read_text())
    launch_name = launch_details.get('launch_name')
    manifest = json.loads((shared_datadir / 'account-vending' / 'manifest.json').read_text())
    puppet_account_id = "098765432101"
    region_name = 'eu-west-1'
    regional_details = {"product_id": "prod-lv3isrxiingdo", "version_id": "pa-yprmofsvvyih4"}
    expected_all_tasks = json.loads((shared_datadir / 'account-vending' / 'all-tasks-for-launch-b.json').read_text())
    mocked_betterboto_client = mocker.patch.object(sut.betterboto_client, 'CrossAccountClientContextManager')
    mocked_describe_provisioning_parameters_response = {
        'ProvisioningArtifactParameters': [
            {'ParameterKey': 'IamUserAccessToBilling'},
            {'ParameterKey': 'Email'},
            {'ParameterKey': 'TargetOU'},
            {'ParameterKey': 'OrganizationAccountAccessRole'},
            {'ParameterKey': 'AccountName'},
            {'ParameterKey': 'AccountVendingCreationLambdaArn'},
            {'ParameterKey': 'AccountVendingBootstrapperLambdaArn'},
        ]
    }
    required_parameters = {
        'IamUserAccessToBilling': True,
        'Email': True,
        'TargetOU': True,
        'OrganizationAccountAccessRole': True,
        'AccountName': True,
        'AccountVendingCreationLambdaArn': True,
        'AccountVendingBootstrapperLambdaArn': True,
    }
    mocked_betterboto_client().__enter__().describe_provisioning_parameters.return_value = mocked_describe_provisioning_parameters_response
    mocked_get_path_for_product = mocker.patch.object(sut.aws, 'get_path_for_product')
    mocked_get_path_for_product.return_value = 1
    mocked_get_parameters_for_launch = mocker.patch.object(sut, 'get_parameters_for_launch')
    mocked_regular_parameters = []
    mocked_ssm_parameters = []
    mocked_get_parameters_for_launch.return_value = (mocked_regular_parameters, mocked_ssm_parameters)

    # exercise
    actual_all_tasks = sut.deploy_launches_task_builder_for_account_launch_region(
        account_id, deployment_map, launch_details, launch_name, manifest,
        puppet_account_id, region_name, regional_details
    )

    # verify
    assert len(actual_all_tasks.keys()) == 1
    assert actual_all_tasks == expected_all_tasks
    mocked_get_path_for_product.assert_called_once_with(
        mocked_betterboto_client().__enter__(), regional_details.get('product_id')
    )
    mocked_get_parameters_for_launch.assert_called_once_with(
        required_parameters,
        deployment_map,
        manifest,
        launch_details,
        account_id,
        launch_details.get('status', constants.PROVISIONED),
    )
