# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from unittest import mock

import pytest
import yaml
from pytest import fixture
import json

from servicecatalog_puppet import constants, luigi_tasks_and_targets


@fixture
def sut():
    from servicecatalog_puppet import manifest_utils
    return manifest_utils


def test_group_by_account_converts_account_ids_numbers_to_strings(sut):
    # setup
    launches = {
        'account-iam-for-prod': {
            'portfolio': 'example-simple-central-it-team-portfolio',
            'product': 'account-iam',
            'version': 'v1',
            'parameters': {
                'RoleName': {
                    'default': 'DevAdmin'
                },
                'Path': {
                    'default': '/human-roles/'
                },
            },
            'deploy_to': {
                'accounts': [
                    {
                        'account_id': '0123456789010',
                        'regions': 'default_region'
                    },
                    {
                        'account_id': 9876543210,
                        'regions': 'default_region'
                    }
                ]
            }
        }
    }
    expected_result = {
        '0123456789010': [
            {
                'deploy_to': {
                    'accounts': [
                        {
                            'account_id': '0123456789010',
                            'regions': 'default_region'
                        },
                        {
                            'account_id': '9876543210',
                            'regions': 'default_region'
                        }
                    ]
                },
                'launch_name': 'account-iam-for-prod',
                'parameters': {
                    'Path': {
                        'default': '/human-roles/'
                    },
                    'RoleName': {
                        'default': 'DevAdmin'
                    }
                },
                'portfolio': 'example-simple-central-it-team-portfolio',
                'product': 'account-iam',
                'version': 'v1'
            }
        ],
        '9876543210': [
            {
                'deploy_to': {
                    'accounts': [
                        {
                            'account_id': '0123456789010',
                            'regions': 'default_region'
                        },
                        {
                            'account_id': '9876543210',
                            'regions': 'default_region'
                        }
                    ]
                },
                'launch_name': 'account-iam-for-prod',
                'parameters': {
                    'Path': {
                        'default': '/human-roles/'
                    },
                    'RoleName': {
                        'default': 'DevAdmin'
                    }
                },
                'portfolio': 'example-simple-central-it-team-portfolio',
                'product': 'account-iam',
                'version': 'v1'
            }
        ]
    }

    # exercise
    actual_result = sut.group_by_account(launches)

    # verify
    assert actual_result == expected_result


def test_build_deployment_map_converts_number_account_ids_into_strings(sut, shared_datadir):
    # setup
    manifest = json.loads((shared_datadir / 'account-vending' / 'manifest_with_numbers.json').read_text())
    section = 'launches'
    expected_result = {
        '456789098673563': {
            'account_id': '456789098673563',
            'default_region': 'eu-west-1',
            'launches': {
                'account-vending-account-creation-shared': {
                    'deploy_to': {
                        'tags': [
                            {
                                'regions': 'default_region',
                                'tag': 'scope:puppet-hub'
                            }
                        ]
                    },
                    'launch_name': 'account-vending-account-creation-shared',
                    'match': 'tag_match',
                    'matching_tag': 'scope:puppet-hub',
                    'outputs': {
                        'ssm': [
                            {
                                'param_name': '/account-vending/account-custom-resource-arn',
                                'stack_output': 'AccountCustomResourceArn'
                            }
                        ]
                    },
                    'parameters': {
                        'AssumableRoleInRootAccountArn': {
                            'default': 'arn:aws:iam::923822062182:role/servicecatalog-puppet/AssumableRoleInRootAccount'
                        }
                    },
                    'portfolio': 'demo-central-it-team-portfolio',
                    'product': 'account-vending-account-creation-shared',
                    'regional_details': {
                        'eu-west-1': {
                            'product_id': 'prod-ahhdj3q5puvhw',
                            'version_id': 'pa-plsqbdtrqt4h2'
                        }
                    },
                    'regions': [
                        'eu-west-1'
                    ],
                    'version': 'v1'
                }
            },
            'name': '456789098673563',
            'regions_enabled': [
                'eu-west-1',
                'eu-west-2'
            ],
            'tags': [
                'type:prod',
                'partition:eu',
                'scope:puppet-hub'
            ]
        },
        '923822062182': {
            'account_id': '923822062182',
            'default_region': 'eu-west-1',
            'launches': {
                'account-vending-account-creation-shared': {
                    'deploy_to': {
                        'tags': [
                            {
                                'regions': 'default_region',
                                'tag': 'scope:puppet-hub'
                            }
                        ]
                    },
                    'launch_name': 'account-vending-account-creation-shared',
                    'match': 'tag_match',
                    'matching_tag': 'scope:puppet-hub',
                    'outputs': {
                        'ssm': [
                            {
                                'param_name': '/account-vending/account-custom-resource-arn',
                                'stack_output': 'AccountCustomResourceArn'
                            }
                        ]
                    },
                    'parameters': {
                        'AssumableRoleInRootAccountArn': {
                            'default': 'arn:aws:iam::923822062182:role/servicecatalog-puppet/AssumableRoleInRootAccount'
                        }
                    },
                    'portfolio': 'demo-central-it-team-portfolio',
                    'product': 'account-vending-account-creation-shared',
                    'regional_details': {
                        'eu-west-1': {
                            'product_id': 'prod-ahhdj3q5puvhw',
                            'version_id': 'pa-plsqbdtrqt4h2'
                        }
                    },
                    'regions': [
                        'eu-west-1'
                    ],
                    'version': 'v1'
                }
            },
            'name': '923822062182',
            'regions_enabled': [
                'eu-west-1',
                'eu-west-2'
            ],
            'tags': [
                'type:prod',
                'partition:eu',
                'scope:puppet-hub'
            ]
        }
    }

    # exercise
    actual_result = sut.build_deployment_map(manifest, section)

    # verify
    assert expected_result == actual_result


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

        ('accounts', 'test_convert_manifest_into_task_defs_handles_default_region'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_enabled'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_regions_enabled'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_enabled_regions'),
        ('accounts', 'test_convert_manifest_into_task_defs_handles_lists'),
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
    mocked_get_regions = mocker.patch.object(sut.cli_command_helpers, 'get_regions')
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

    # exercise
    with pytest.raises(Exception) as e:
        actual_result = sut.convert_manifest_into_task_defs_for_launches(manifest, puppet_account_id, should_use_sns)

    # verify
    assert str(e.exconly()) == "Exception: Unsupported regions foo setting for launch: assumable-role-account"


@pytest.mark.parametrize(
    "manifest_file",
    [
        'test_convert_manifest_into_task_defs_handles_depends_on_without-leaks',
    ]
)
def test_convert_manifest_into_task_defs_handles_for_unsupported_string(sut, shared_datadir, manifest_file, mocker):
    # setup
    manifest = yaml.safe_load(
        (shared_datadir / 'manifest_utils' / f"{manifest_file}.yaml").read_text()
    )
    puppet_account_id = 9
    should_use_sns = True
    should_use_product_plans = True
    mocked_get_regions = mocker.patch.object(sut.cli_command_helpers, 'get_regions')
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
