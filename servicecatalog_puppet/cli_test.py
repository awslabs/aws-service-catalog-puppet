# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pytest import fixture
import pkg_resources

@fixture
def sut():
    from servicecatalog_puppet import cli
    return cli


def test_placeholder(sut):
    assert True == True

