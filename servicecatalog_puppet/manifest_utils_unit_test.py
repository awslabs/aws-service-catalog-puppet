#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import unittest
from copy import deepcopy
from unittest import skip

import constants


class TestManifest(unittest.TestCase):
    account_a = {
        "account_id": "012345678910",
        "default_region": "eu-west-1",
        "name": "accounta",
        "expanded_from": "ou-aaaa-aaaaaaaa",
        "organization": "o-aaaaaaaa",
        "regions_enabled": ["eu-west-2",],
        "tags": ["group:A"],
    }
    account_b = {
        "account_id": "009876543210",
        "default_region": "us-west-1",
        "expanded_from": "ou-bbbb-bbbbbbbb",
        "organization": "o-bbbbbbbb",
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
    accounts = {"accounts": [account_a, account_b, account_c,]}
    launch_a = {
        "portfolio": "portfolio_a",
        "product": "product_a",
        "execution": "hub",
        "version": "version_a",
        "deploy_to": {"tags": [{"regions": "default_region", "tag": "group:A"}]},
    }
    assertion_a = {
        "expected": {"foo": "bar"},
        "actual": {"bar": "foo"},
        "assert_for": {"tags": [{"regions": "default_region", "tag": "group:A"}]},
    }
    spoke_local_portfolio_a = {
        "portfolio": "portfolio_a",
        "deploy_to": {"tags": [{"regions": "default_region", "tag": "group:A"}]},
    }
    launch_b = {
        "portfolio": "portfolio_b",
        "product": "product_b",
        "version": "version_b",
        "execution": "hub",
        "deploy_to": {"tags": [{"regions": "default_region", "tag": "group:B"}]},
    }
    launch_c = {
        "portfolio": "portfolio_c",
        "product": "product_c",
        "version": "version_c",
        "execution": "hub",
        "deploy_to": {"tags": [{"regions": "enabled_regions", "tag": "group:B"}]},
    }
    launches = dict(
        launches=dict(launch_a=launch_a, launch_b=launch_b, launch_c=launch_c)
    )
    assertions = dict(assertions=dict(assertion_a=assertion_a))
    spoke_local_portfolios = {
        "spoke-local-portfolios": dict(spoke_local_portfolio_a=spoke_local_portfolio_a)
    }
    puppet_account_id = "0123456789010"

    def setUp(self):
        from servicecatalog_puppet.manifest_utils import Manifest

        self.sut = Manifest()

    def tearDown(self):
        self.sut = None

    def test_get_provisioning_tasks_for_launch_and_region_for_tags(self):
        # setup
        puppet_account_id = "pppppppppppp"
        section_name = "launches"
        item_name = "launch_a"
        region = "eu-west-1"
        self.sut.update(deepcopy(self.accounts))
        self.sut.update(deepcopy(self.launches))
        expected_result = [
            {
                "account_id": "012345678910",
                "account_parameters": {},
                "execution": "hub",
                "launch_name": item_name,
                "launch_parameters": {},
                "manifest_parameters": {},
                "portfolio": "portfolio_a",
                "product": "product_a",
                "puppet_account_id": puppet_account_id,
                "region": region,
                "ssm_param_outputs": [],
                "requested_priority": 0,
                "version": "version_a",
            }
        ]

        # exercise
        actual_results = self.sut.get_tasks_for_launch_and_region(
            puppet_account_id, section_name, item_name, region
        )

        # verify
        self.assertListEqual(expected_result, actual_results)

    def test_get_provisioning_tasks_for_spoke_local_portfolios_and_region_for_tags(
        self,
    ):
        # setup
        puppet_account_id = "pppppppppppp"
        section_name = "spoke-local-portfolios"
        item_name = "spoke_local_portfolio_a"
        region = "eu-west-1"
        self.sut.update(deepcopy(self.accounts))
        self.sut.update(deepcopy(self.launches))
        self.sut.update(deepcopy(self.spoke_local_portfolios))
        expected_result = [
            {
                "account_id": "012345678910",
                "spoke_local_portfolio_name": item_name,
                "portfolio": "portfolio_a",
                "puppet_account_id": puppet_account_id,
                "region": region,
                "associations": [],
                "launch_constraints": [],
                "organization": "",
                "product_generation_method": "copy",
                "sharing_mode": "ACCOUNT",
            }
        ]

        # exercise
        actual_results = self.sut.get_tasks_for_launch_and_region(
            puppet_account_id, section_name, item_name, region
        )

        # verify
        self.assertListEqual(expected_result, actual_results)

    def test_get_provisioning_tasks_for_launch_and_region_for_accounts(self):
        # setup
        puppet_account_id = "pppppppppppp"
        section_name = "launches"
        item_name = "launch_a"
        region = "eu-west-2"
        self.sut.update(deepcopy(self.accounts))
        self.sut.update(deepcopy(self.launches))
        self.sut[section_name][item_name]["deploy_to"] = dict(
            accounts=[dict(account_id="012345678910", regions="enabled_regions")]
        )
        expected_result = [
            {
                "account_id": "012345678910",
                "account_parameters": {},
                "execution": "hub",
                "launch_name": item_name,
                "launch_parameters": {},
                "manifest_parameters": {},
                "portfolio": "portfolio_a",
                "product": "product_a",
                "puppet_account_id": puppet_account_id,
                "region": region,
                "ssm_param_outputs": [],
                "requested_priority": 0,
                "version": "version_a",
            }
        ]

        # exercise
        actual_results = self.sut.get_tasks_for_launch_and_region(
            puppet_account_id, section_name, item_name, region
        )

        # verify
        self.assertListEqual(expected_result, actual_results)

    def test_get_assertion_tasks_for_launch_and_region_for_accounts(self):
        # setup
        puppet_account_id = "pppppppppppp"
        section_name = "assertions"
        item_name = "assertion_a"
        region = "eu-west-1"
        self.sut.update(deepcopy(self.accounts))
        self.sut.update(deepcopy(self.assertions))

        expected_result = [
            {
                "account_id": "012345678910",
                "assertion_name": item_name,
                "puppet_account_id": puppet_account_id,
                "region": region,
                "execution": constants.EXECUTION_MODE_DEFAULT,
                "requested_priority": 0,
                "expected": {"foo": "bar"},
                "actual": {"bar": "foo"},
            }
        ]

        # exercise
        actual_results = self.sut.get_tasks_for_launch_and_region(
            puppet_account_id, section_name, item_name, region
        )

        # verify
        self.assertListEqual(expected_result, actual_results)

    def test_get_regions_used_for_section_item_for_tags_and_default_region(self):
        # setup
        puppet_account_id = "01234567890"
        section_name = "launches"
        item_name = "launch_a"
        self.sut.update(deepcopy(self.accounts))
        self.sut.get("accounts").append(
            {
                "account_id": "9875983465794387",
                "default_region": "eu-west-3",
                "name": "accounta",
                "expanded_from": "ou-aaaa-aaaaaaaa",
                "organization": "o-aaaaaaaa",
                "regions_enabled": ["eu-west-2",],
                "tags": ["group:A"],
            }
        )
        self.sut.update(deepcopy(self.launches))
        expected_result = ["eu-west-1", "eu-west-3"]

        # exercise
        actual_results = self.sut.get_regions_used_for_section_item(
            puppet_account_id, section_name, item_name
        )
        actual_results.sort()

        # verify
        self.assertListEqual(expected_result, actual_results)

    def test_get_regions_used_for_section_item_for_accounts_and_default_region(self):
        # setup
        puppet_account_id = "01234567890"
        section_name = "launches"
        item_name = "launch_a"
        self.sut.update(deepcopy(self.accounts))
        self.sut.get("accounts").append(
            {
                "account_id": "9875983465794387",
                "default_region": "eu-west-99",
                "name": "accounta",
                "expanded_from": "ou-aaaa-aaaaaaaa",
                "organization": "o-aaaaaaaa",
                "regions_enabled": ["eu-west-2",],
                "tags": ["group:A"],
            }
        )
        self.sut.update(deepcopy(self.launches))
        self.sut["launches"][item_name]["deploy_to"] = dict(
            accounts=[dict(account_id="9875983465794387", regions="default_region")]
        )
        expected_result = ["eu-west-99"]

        # exercise
        actual_results = self.sut.get_regions_used_for_section_item(
            puppet_account_id, section_name, item_name
        )

        # verify
        self.assertListEqual(expected_result, actual_results)

    def test_get_regions_used_for_section_item_for_enabled_region(self):
        # setup
        puppet_account_id = "01234567890"
        section_name = "launches"
        item_name = "launch_c"
        self.sut.update(deepcopy(self.accounts))
        self.sut.get("accounts").append(
            {
                "account_id": "9875983465794387",
                "default_region": "eu-west-3",
                "name": "accounta",
                "expanded_from": "ou-aaaa-aaaaaaaa",
                "organization": "o-aaaaaaaa",
                "regions_enabled": ["eu-west-2",],
                "tags": ["group:A"],
            }
        )
        self.sut.update(deepcopy(self.launches))
        expected_result = ["us-west-2"]

        # exercise
        actual_results = self.sut.get_regions_used_for_section_item(
            puppet_account_id, section_name, item_name
        )

        # verify
        self.assertListEqual(expected_result, actual_results)

    def test_get_accounts_by_region(self):
        # setup
        self.sut.update(deepcopy(self.accounts))
        expected_regions = [
            "eu-west-1",
            "eu-west-2",
            "us-west-1",
            "us-west-2",
            "ap-west-1",
            "ap-west-2",
        ]

        # exercise
        actual_result = self.sut.get_accounts_by_region()
        actual_regions = list(actual_result.keys())

        # verify
        self.assertCountEqual(expected_regions, actual_regions)
        self.assertEqual(actual_result.get("eu-west-1"), [self.account_a])
        self.assertIsNone(actual_result.get("eu-west-999"))

    @skip
    def test_get_shares_by_region_portfolio_account(self):
        # setup
        self.sut.update(deepcopy(self.accounts))
        self.sut.update(deepcopy(self.launches))

        # exercise
        actual_result = self.sut.get_shares_by_region_portfolio_account(
            self.puppet_account_id, "launches"
        )

        # verify
        self.assertIsNotNone(actual_result.get("eu-west-1").get("portfolio_a"))
        self.assertEqual(
            actual_result.get("eu-west-1").get("portfolio_a").get("012345678910"),
            self.account_a,
        )
        self.assertIsNotNone(actual_result.get("us-west-1").get("portfolio_b"))
        self.assertEqual(
            actual_result.get("us-west-1").get("portfolio_b").get("009876543210"),
            self.account_b,
        )

    def test_get_sharing_policies_by_region(self):
        # setup
        self.sut.update(deepcopy(self.accounts))
        self.sut.update(deepcopy(self.launches))

        # exercise
        actual_result = self.sut.get_sharing_policies_by_region()

        # verify
        self.assertIsNotNone(actual_result.get("eu-west-1"))
        self.assertEqual(
            actual_result.get("eu-west-1"),
            dict(organizations=["o-aaaaaaaa"], accounts=[]),
        )
        self.assertEqual(
            actual_result.get("us-west-1"),
            dict(organizations=["o-bbbbbbbb"], accounts=[]),
        )
        self.assertEqual(
            actual_result.get("ap-west-1"),
            dict(organizations=[], accounts=["432100098765"]),
        )
