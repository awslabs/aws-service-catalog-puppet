# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from unittest import mock

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
                            'default':'arn:aws:iam::923822062182:role/servicecatalog-puppet/AssumableRoleInRootAccount'
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
