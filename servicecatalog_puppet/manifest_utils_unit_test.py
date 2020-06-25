# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import unittest
from pytest import fixture


class TestManifest(unittest.TestCase):
    account_a = {
        'account_id': '012345678910',
        'default_region': 'eu-west-1',
        'name': 'accounta',
        'expanded_from': 'ou-aaaa-aaaaaaaa',
        'organization': 'o-aaaaaaaa',
        'regions_enabled': [
            'eu-west-2',
        ],
        'tags': [
            'group:A'
        ]
    }
    account_b = {
        'account_id': '009876543210',
        'default_region': 'us-west-1',
        'expanded_from': 'ou-bbbb-bbbbbbbb',
        'organization': 'o-bbbbbbbb',
        'name': 'accountb',
        'regions_enabled': [
            'us-west-2',
        ],
        'tags': [
            'group:B'
        ]

    }
    account_c = {
        'account_id': '432100098765',
        'default_region': 'ap-west-1',
        'name': 'accountc',
        'regions_enabled': [
            'ap-west-2',
        ],
        'tags': [
            'group:C'
        ]

    }
    accounts = {'accounts': [account_a, account_b, account_c, ]}
    launch_a = {
        'portfolio': 'portfolio_a',
        'product': 'product_a',
        'version': 'version_a',
        'deploy_to': {
            'tags': [
                {
                    'regions': 'default_region',
                    'tag': 'group:A'
                }
            ]
        }
    }
    launch_b = {
        'portfolio': 'portfolio_b',
        'product': 'product_b',
        'version': 'version_b',
        'deploy_to': {
            'tags': [
                {
                    'regions': 'default_region',
                    'tag': 'group:B'
                }
            ]
        }
    }
    launches = dict(launches=dict(launch_a=launch_a, launch_b=launch_b))

    def setUp(self):
        from servicecatalog_puppet.manifest_utils import Manifest
        self.sut = Manifest()

    def tearDown(self):
        self.sut = None

    def test_get_accounts_by_region(self):
        # setup
        self.sut.update(self.accounts)
        expected_regions = ['eu-west-1', 'eu-west-2', 'us-west-1', 'us-west-2', 'ap-west-1', 'ap-west-2']

        # exercise
        actual_result = self.sut.get_accounts_by_region()
        actual_regions = list(actual_result.keys())

        # verify
        self.assertCountEqual(expected_regions, actual_regions)
        self.assertEqual(actual_result.get('eu-west-1'), [self.account_a])
        self.assertIsNone(actual_result.get('eu-west-999'))

    def test_get_shares_by_region_portfolio_account(self):
        # setup
        self.sut.update(self.accounts)
        self.sut.update(self.launches)

        # exercise
        actual_result = self.sut.get_shares_by_region_portfolio_account()

        # verify
        self.assertIsNotNone(actual_result.get('eu-west-1').get('portfolio_a'))
        self.assertEqual(actual_result.get('eu-west-1').get('portfolio_a').get('012345678910'), self.account_a)
        self.assertIsNotNone(actual_result.get('us-west-1').get('portfolio_b'))
        self.assertEqual(actual_result.get('us-west-1').get('portfolio_b').get('009876543210'), self.account_b)

    def test_get_sharing_policies_by_region(self):
        # setup
        self.sut.update(self.accounts)
        self.sut.update(self.launches)

        # exercise
        actual_result = self.sut.get_sharing_policies_by_region()

        # verify
        self.assertIsNotNone(actual_result.get('eu-west-1'))
        self.assertEqual(actual_result.get('eu-west-1'), dict(organizations=['o-aaaaaaaa'], accounts=[]))
        self.assertEqual(actual_result.get('us-west-1'), dict(organizations=['o-bbbbbbbb'], accounts=[]))
        self.assertEqual(actual_result.get('ap-west-1'), dict(organizations=[], accounts=['432100098765']))