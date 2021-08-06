#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from unittest import mock as mocker
from unittest.mock import call


def test_resolve_from_site_packages():
    # setup
    from servicecatalog_puppet import asset_helpers as sut

    expected_result = os.path.sep.join(
        [os.path.dirname(os.path.abspath(__file__)), "foo"]
    )

    # exercise
    actual_result = sut.resolve_from_site_packages("foo")

    # verify
    assert actual_result == expected_result


@mocker.patch("builtins.open", new_callable=mocker.MagicMock())
def test_read_from_site_packages(mocked_open):
    # setup
    from servicecatalog_puppet import asset_helpers as sut

    expected_param = os.path.sep.join(
        [os.path.dirname(os.path.abspath(__file__)), "foo"]
    )

    # exercise
    sut.read_from_site_packages("foo")

    # verify
    assert mocked_open.call_count == 1
    assert mocked_open.call_args == call(expected_param, "r")
