# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import pytest
import yaml
from pytest import fixture
import json


@fixture
def sut():
    from servicecatalog_puppet import manifest_utils
    return manifest_utils


def test_convert_manifest_into_task_defs(sut, shared_datadir):
    # setup
    manifest = json.loads((shared_datadir / 'account-vending' / 'manifest.json').read_text())
    puppet_account_id = 9
    expected_result = json.loads((shared_datadir / 'account-vending' / 'manifest-tasks.json').read_text())
    should_use_sns = True
    should_use_product_plans = True

    # execute
    actual_result = sut.convert_manifest_into_task_defs_for_launches(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans
    )

    # verify
    assert actual_result == expected_result
    assert len(actual_result) == len(expected_result)


@pytest.mark.parametrize(
    "dir,manifest_file",
    [
        ('tags', 'test_convert_manifest_into_task_defs_handles_default_region'),
        ('tags', 'test_convert_manifest_into_task_defs_handles_enabled'),
        ('tags', 'test_convert_manifest_into_task_defs_handles_regions_enabled'),
        ('tags', 'test_convert_manifest_into_task_defs_handles_enabled_regions'),
        ('tags', 'test_convert_manifest_into_task_defs_handles_lists'),
        ('tags', 'test_convert_manifest_into_task_defs_handles_empty'),

        ('accounts', 'test_convert_manifest_into_task_defs_handles_default_region'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_enabled'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_regions_enabled'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_enabled_regions'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_lists'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_empty'),
    ]
)
def test_convert_manifest_into_task_defs_handles_default_region(sut, shared_datadir, dir, manifest_file):
    # setup
    manifest = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / dir / f"{manifest_file}.yaml").read_text()
    )
    puppet_account_id = 9
    should_use_sns = True
    should_use_product_plans = True
    expected_result = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / dir / f"{manifest_file}_expected.yaml").read_text()
    )

    # exercise
    actual_result = sut.convert_manifest_into_task_defs_for_launches(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans
    )

    # verify
    assert expected_result == actual_result


@pytest.mark.parametrize(
    "dir,manifest_file",
    [
        ('tags', 'test_convert_manifest_into_task_defs_handles_all'),

        ('accounts', 'test_convert_manifest_into_task_defs_handles_all'),
    ]
)
def test_convert_manifest_into_task_defs_handles_default_region_for_all(sut, mocker, shared_datadir, dir,
                                                                        manifest_file):
    # setup
    manifest = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / dir / f"{manifest_file}.yaml").read_text()
    )
    puppet_account_id = 9
    should_use_sns = True
    should_use_product_plans = True
    expected_result = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / dir / f"{manifest_file}_expected.yaml").read_text()
    )
    mocked_get_regions = mocker.patch.object(sut.config, 'get_regions')
    mocked_get_regions.return_value = [
        'eu-west-3',
    ]

    # exercise
    actual_result = sut.convert_manifest_into_task_defs_for_launches(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans
    )

    # verify
    assert expected_result == actual_result


@pytest.mark.parametrize(
    "dir,manifest_file",
    [
        ('tags', 'test_convert_manifest_into_task_defs_handles_unsupported_string'),

        ('accounts', 'test_convert_manifest_into_task_defs_handles_unsupported_string'),
    ]
)
def test_convert_manifest_into_task_defs_handles_for_unsupported_string(sut, shared_datadir, dir, manifest_file):
    # setup
    manifest = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / dir / f"{manifest_file}.yaml").read_text()
    )
    puppet_account_id = 9
    should_use_sns = True
    should_use_product_plans = True

    # exercise
    with pytest.raises(Exception) as e:
        sut.convert_manifest_into_task_defs_for_launches(
            manifest, puppet_account_id, should_use_sns, should_use_product_plans
        )

    # verify
    assert str(e.exconly()) == "Exception: Unsupported regions foo setting for launch: assumable-role-account"


@pytest.mark.parametrize(
    "manifest_file",
    [
        'test_convert_manifest_into_task_defs_handles_depends_on_without-leaks',
    ]
)
def test_convert_manifest_into_task_defs_handles_transient_dependencies(sut, shared_datadir, manifest_file, mocker):
    # setup
    manifest = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / f"{manifest_file}.yaml").read_text()
    )
    puppet_account_id = 9
    should_use_sns = True
    should_use_product_plans = True
    mocked_get_regions = mocker.patch.object(sut.config, 'get_regions')
    mocked_get_regions.return_value = [
        'eu-west-3',
    ]
    verified = False
    expected_result = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / f"{manifest_file}_expected.yaml").read_text()
    )

    # exercise
    actual_result = sut.convert_manifest_into_task_defs_for_launches(
        manifest, puppet_account_id, should_use_sns, should_use_product_plans
    )

    # verify
    for task_def in actual_result:
        launch_name = task_def.get('launch_name')
        if launch_name == 'assumable-role-account-child':
            dependencies = task_def.get('dependencies')
            assert len(dependencies) == 1
            transient_dependencies = dependencies[0].get('dependencies')
            assert len(transient_dependencies) == 0
            verified = True

    assert verified
    assert actual_result == expected_result
