# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import unittest
from unittest.mock import MagicMock
from copy import deepcopy

from servicecatalog_puppet import constants


class TestManifestForExpand(unittest.TestCase):

    organization_id = "o-aaaaaaaa"

    account_a = {
        "account_id": "012345678910",
        "default_region": "eu-west-1",
        "name": "accounta",
        "regions_enabled": ["eu-west-2",],
        "tags": ["group:A"],
    }
    account_b = {
        "account_id": "009876543210",
        "default_region": "us-west-1",
        "name": "accountb",
        "regions_enabled": ["us-west-2",],
        "tags": ["group:B"],
    }
    account_c = {
        "account_id": "432100098765",
        "default_region": "ap-west-1",
        "name": "accountc",
        "regions_enabled": ["ap-west-2",],
        "tags": ["group:C"],
    }
    accounts = [
        account_a,
        account_b,
        account_c,
    ]

    account_ou_a = {
        "ou": "ou-aaaa-aaaaaaaa",
        "default_region": "eu-west-1",
        "name": "oua",
        "regions_enabled": ["eu-west-2",],
        "tags": ["group:A"],
    }
    account_ou_b = {
        "ou": "/OrgUnitB",
        "default_region": "us-west-1",
        "name": "oub",
        "regions_enabled": ["us-west-2",],
        "tags": ["group:B"],
    }
    account_ou_c = {
        "ou": "ou-aaaa-cccccccc",
        "default_region": "ap-west-1",
        "name": "ouc",
        "regions_enabled": ["ap-west-2",],
        "tags": ["group:C"],
    }

    org_units = [
        account_ou_a,
        account_ou_b,
        account_ou_c,
    ]

    def setUp(self):
        self.maxDiff = None
        from servicecatalog_puppet import manifest_utils

        self.client_mock = MagicMock()

        self.sut = manifest_utils.expand_manifest

    def tearDown(self):
        self.sut = None
        self.client_mock = None

    def test_expand_for_single_account_in_ou(self):
        # setup
        expanded_manifest = dict()
        expanded_manifest[constants.ACCOUNTS] = self.accounts
        expanded_manifest[constants.LAUNCHES] = dict()
        expanded_manifest[constants.STACKS] = dict()
        expanded_manifest[constants.SPOKE_LOCAL_PORTFOLIOS] = dict()
        expanded_manifest[constants.ACTIONS] = dict()
        expanded_manifest[constants.ASSERTIONS] = dict()
        expanded_manifest[constants.LAMBDA_INVOCATIONS] = dict()

        expected_results = deepcopy(expanded_manifest)
        for account in expected_results[constants.ACCOUNTS]:
            account_id = account["account_id"]
            account["email"] = f"{account_id}@test.com"
            account["organization"] = self.organization_id

        def describe_account_side_effect(AccountId):
            return {
                "Account": {
                    "Id": AccountId,
                    "Arn": f"arn:aws:organizations::000000000000:account/{self.organization_id}/{AccountId}",
                    "Email": f"{AccountId}@test.com",
                    "Status": "ACTIVE",
                }
            }

        self.client_mock.describe_account = MagicMock(
            side_effect=describe_account_side_effect
        )

        # exercise
        actual_results = self.sut(expanded_manifest, self.client_mock)

        # verify
        self.assertDictEqual(expected_results, actual_results)

    def test_expand_for_ou(self):
        # setup
        expanded_manifest = dict()
        expanded_manifest[constants.ACCOUNTS] = self.org_units
        expanded_manifest[constants.LAUNCHES] = dict()
        expanded_manifest[constants.STACKS] = dict()
        expanded_manifest[constants.SPOKE_LOCAL_PORTFOLIOS] = dict()
        expanded_manifest[constants.ACTIONS] = dict()
        expanded_manifest[constants.ASSERTIONS] = dict()
        expanded_manifest[constants.LAMBDA_INVOCATIONS] = dict()

        expected_results = deepcopy(expanded_manifest)
        accounts = []

        account_a = deepcopy(self.account_a)
        account_a["email"] = f"{account_a['account_id']}@test.com"
        account_a["organization"] = self.organization_id
        account_a["expanded_from"] = "ou-aaaa-aaaaaaaa"
        account_a["name"] = account_a["account_id"]
        accounts.append(account_a)

        account_b = deepcopy(self.account_b)
        account_b["email"] = f"{account_b['account_id']}@test.com"
        account_b["organization"] = self.organization_id
        account_b["expanded_from"] = "ou-aaaa-bbbbbbbb"
        account_b["name"] = account_b["account_id"]
        accounts.append(account_b)

        account_c = deepcopy(self.account_c)
        account_c["email"] = f"{account_c['account_id']}@test.com"
        account_c["organization"] = self.organization_id
        account_c["expanded_from"] = "ou-aaaa-cccccccc"
        account_c["name"] = account_c["account_id"]
        accounts.append(account_c)

        expected_results[constants.ACCOUNTS] = accounts

        def describe_account_side_effect(AccountId):
            return {
                "Account": {
                    "Id": AccountId,
                    "Arn": f"arn:aws:organizations::000000000000:account/{self.organization_id}/{AccountId}",
                    "Email": f"{AccountId}@test.com",
                    "Status": "ACTIVE",
                    "Name": AccountId,
                }
            }

        def list_children_nested_side_effect(ParentId, ChildType):
            ou_mapping = {
                "ou-aaaa-aaaaaaaa": [{"Id": "012345678910"}],
                "ou-aaaa-bbbbbbbb": [{"Id": "009876543210"}],
                "ou-aaaa-cccccccc": [{"Id": "432100098765"}],
            }
            return ou_mapping.get(ParentId, [])

        self.client_mock.describe_account = MagicMock(
            side_effect=describe_account_side_effect
        )
        self.client_mock.list_children_nested = MagicMock(
            side_effect=list_children_nested_side_effect
        )
        self.client_mock.convert_path_to_ou = MagicMock(return_value="ou-aaaa-bbbbbbbb")

        # exercise
        actual_results = self.sut(expanded_manifest, self.client_mock)

        # verify
        self.assertDictEqual(expected_results, actual_results)
