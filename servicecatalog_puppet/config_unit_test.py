# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import yaml
from pytest import fixture
import pytest

from . import constants


@fixture
def sut():
    from . import config

    return config


def test_get_config_without_a_default_region(sut, mocker):
    # setup
    expected_result = {
        "Foo": "Bar",
    }
    mocked_get_home_region = mocker.patch.object(sut, "get_home_region")
    fake_home_region = "eu-west-9"
    mocked_get_home_region.return_value = fake_home_region
    mocked_response = {"Parameter": {"Value": yaml.safe_dump(expected_result)}}
    mocked_betterboto_client = mocker.patch.object(
        sut.betterboto_client, "CrossAccountClientContextManager"
    )
    mocked_betterboto_client().__enter__().get_parameter.return_value = mocked_response
    puppet_account_id = ""

    # exercise
    actual_result = sut.get_config(puppet_account_id)

    # verify
    assert actual_result == expected_result
    args, kwargs = mocked_betterboto_client.call_args
    assert "ssm" == args[0]
    assert {"region_name": fake_home_region} == kwargs


def test_get_config_with_a_default_region(sut, mocker):
    # setup
    expected_result = {
        "Foo": "Bar",
    }
    fake_home_region = "eu-west-10"
    mocked_response = {"Parameter": {"Value": yaml.safe_dump(expected_result)}}
    mocked_betterboto_client = mocker.patch.object(
        sut.betterboto_client, "CrossAccountClientContextManager"
    )
    mocked_betterboto_client().__enter__().get_parameter.return_value = mocked_response

    # exercise
    actual_result = sut.get_config(
        puppet_account_id="", default_region=fake_home_region
    )

    # verify
    assert actual_result == expected_result
    args, kwargs = mocked_betterboto_client.call_args
    assert "ssm" == args[0]
    assert {"region_name": fake_home_region} == kwargs


@pytest.mark.parametrize(
    "method_to_call,key,expected_result",
    [
        ("get_regions", "regions", ["eu-west-1", "eu-west-3",]),
        ("get_should_use_sns", "should_collect_cloudformation_events", True),
        ("get_should_use_eventbridge", "should_forward_events_to_eventbridge", True),
        (
            "get_should_forward_failures_to_opscenter",
            "should_forward_failures_to_opscenter",
            True,
        ),
        ("get_should_use_product_plans", "should_use_product_plans", True),
    ],
)
def test_get_some_config(sut, mocker, method_to_call, key, expected_result):
    # setup
    default_region = "eu-west-10"
    mocked_get_config = mocker.patch.object(sut, "get_config")
    mocked_get_config.return_value = {key: expected_result}

    # exercise
    f = getattr(sut, method_to_call)
    actual_result = f("", default_region)

    # verify
    args, kwargs = mocked_get_config.call_args
    assert expected_result == actual_result
    assert args == ("", default_region,)
    assert kwargs == {}


def test_get_home_region(sut, mocker):
    # setup
    expected_result = {
        "us-east-3",
    }
    mocked_response = {"Parameter": {"Value": expected_result}}
    mocked_betterboto_client = mocker.patch.object(
        sut.betterboto_client, "CrossAccountClientContextManager"
    )
    mocked_betterboto_client().__enter__().get_parameter.return_value = mocked_response
    puppet_account_id = ""

    # exercise
    actual_result = sut.get_home_region(puppet_account_id)

    # verify
    assert actual_result == expected_result
    args, kwargs = mocked_betterboto_client.call_args
    assert "ssm" == args[0]
    assert {} == kwargs
    args, kwargs = mocked_betterboto_client().__enter__().get_parameter.call_args
    assert args == ()
    assert kwargs == {"Name": constants.HOME_REGION_PARAM_NAME}


def test_get_org_iam_role_arn(sut, mocker):
    # setup
    expected_result = "some_fake_arn"
    mocked_response = {"Parameter": {"Value": expected_result}}
    mocked_betterboto_client = mocker.patch.object(
        sut.betterboto_client, "CrossAccountClientContextManager"
    )
    mocked_betterboto_client().__enter__().get_parameter.return_value = mocked_response
    mocked_get_home_region = mocker.patch.object(sut, "get_home_region")
    mocked_get_home_region.return_value = "us-east-9"
    puppet_account_id = ""

    # exercise
    actual_result = sut.get_org_iam_role_arn(puppet_account_id)

    # verify
    assert actual_result == expected_result
    args, kwargs = mocked_betterboto_client().__enter__().get_parameter.call_args
    assert args == ()
    assert kwargs == {"Name": constants.CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN}


def test_get_puppet_account_id(sut, mocker):
    # setup
    expected_result = "some_fake_arn"
    mocked_response = {"Account": expected_result}
    mocked_betterboto_client = mocker.patch.object(
        sut.betterboto_client, "ClientContextManager"
    )
    mocked_betterboto_client().__enter__().get_caller_identity.return_value = (
        mocked_response
    )

    # exercise
    actual_result = sut.get_puppet_account_id()

    # verify
    assert actual_result == expected_result
