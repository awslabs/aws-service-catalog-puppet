#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from unittest import mock as mocker

import yaml

from servicecatalog_puppet import constants


@mocker.patch("servicecatalog_puppet.config.get_home_region")
@mocker.patch(
    "servicecatalog_puppet.config.betterboto_client.CrossAccountClientContextManager"
)
def test_get_config_without_a_default_region(
    mocked_betterboto_client, mocked_get_home_region
):
    # setup
    from servicecatalog_puppet import config as sut

    expected_result = {
        "Foo": "Bar",
    }
    fake_home_region = "eu-west-9"
    mocked_get_home_region.return_value = fake_home_region
    mocked_response = {"Parameter": {"Value": yaml.safe_dump(expected_result)}}
    mocked_betterboto_client.return_value.__enter__.return_value.get_parameter.return_value = (
        mocked_response
    )
    puppet_account_id = ""

    # exercise
    actual_result = sut.get_config(puppet_account_id)

    # verify
    assert actual_result == expected_result
    args, kwargs = mocked_betterboto_client.call_args
    assert "ssm" == args[0]
    assert {"region_name": fake_home_region} == kwargs


@mocker.patch(
    "servicecatalog_puppet.config.betterboto_client.CrossAccountClientContextManager"
)
def test_get_config_with_a_default_region(mocked_betterboto_client):
    # setup
    from servicecatalog_puppet import config as sut

    expected_result = {
        "Foo": "Bar",
    }
    fake_home_region = "eu-west-10"
    mocked_response = {"Parameter": {"Value": yaml.safe_dump(expected_result)}}
    mocked_betterboto_client.return_value.__enter__.return_value.get_parameter.return_value = (
        mocked_response
    )

    # exercise
    actual_result = sut.get_config(
        puppet_account_id="", default_region=fake_home_region
    )

    # verify
    assert actual_result == expected_result
    args, kwargs = mocked_betterboto_client.call_args
    assert "ssm" == args[0]
    assert {"region_name": fake_home_region} == kwargs


@mocker.patch(
    "servicecatalog_puppet.config.betterboto_client.CrossAccountClientContextManager"
)
def test_get_org_iam_role_arn(mocked_betterboto_client):
    # setup
    from servicecatalog_puppet import config as sut

    expected_result = "some_fake_arn"
    mocked_response = {"Parameter": {"Value": expected_result}}
    mocked_betterboto_client.return_value.__enter__.return_value.get_parameter.return_value = (
        mocked_response
    )
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
