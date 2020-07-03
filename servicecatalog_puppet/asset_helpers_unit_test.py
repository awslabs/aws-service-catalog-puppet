# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import call

from pytest import fixture
import os


@fixture
def sut():
    from . import asset_helpers

    return asset_helpers


def test_resolve_from_site_packages(sut):
    # setup
    expected_result = os.path.sep.join(
        [os.path.dirname(os.path.abspath(__file__)), "foo"]
    )

    # exercise
    actual_result = sut.resolve_from_site_packages("foo")

    # verify
    assert actual_result == expected_result


def test_read_from_site_packages(sut, mocker):
    # setup
    mocked_open = mocker.patch.object(sut, "open")
    expected_param = os.path.sep.join(
        [os.path.dirname(os.path.abspath(__file__)), "foo"]
    )

    # exercise
    sut.read_from_site_packages("foo")

    # verify
    assert mocked_open.call_count == 1
    assert mocked_open.call_args == call(expected_param, "r")
    # assert mocked_open.assert_called_once_with(expected_param)
