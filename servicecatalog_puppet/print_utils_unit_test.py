#   Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: Apache-2.0
from unittest import mock


@mock.patch("click.secho")
def test_echo(mocked_click_secho):
    # setup
    from servicecatalog_puppet import print_utils

    message = "hello world"

    # exercise
    print_utils.echo(message)

    # verify
    mocked_click_secho.assert_called_once_with(message)


@mock.patch("click.secho")
def test_warn(mocked_click_secho):
    from servicecatalog_puppet import print_utils

    message = "hello world"

    # exercise
    print_utils.warn(message)

    # verify
    mocked_click_secho.assert_called_once_with(
        message, err=True, fg="yellow",
    )


@mock.patch("click.secho")
def test_error(mocked_click_secho):
    from servicecatalog_puppet import print_utils

    message = "hello world"

    # exercise
    print_utils.error(message)

    # verify
    mocked_click_secho.assert_called_once_with(
        message, err=True, fg="red",
    )
