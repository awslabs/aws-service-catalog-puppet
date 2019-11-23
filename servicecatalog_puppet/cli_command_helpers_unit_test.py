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
