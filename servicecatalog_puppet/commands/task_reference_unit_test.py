#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from unittest import mock as mocker
from unittest.mock import call


@mocker.patch("servicecatalog_puppet.config", new_callable=mocker.MagicMock())
@mocker.patch("builtins.open", new_callable=mocker.MagicMock())
def test_generate_complete_task_reference_for_empty_manifest(
    open_mocked, config_mocked
):
    # setup
    from servicecatalog_puppet.commands import task_reference

    f = mocker.MagicMock()
    puppet_account_id = "012345678910"
    manifest = dict()
    expected_result = dict(all_tasks=dict())

    # exercise
    actual_result = task_reference.generate_complete_task_reference(
        f, puppet_account_id, manifest
    )

    # verify
    assert actual_result == expected_result
